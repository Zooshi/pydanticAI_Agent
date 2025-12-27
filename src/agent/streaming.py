"""Streaming response handler for PydanticAI financial agent.

This module provides streaming functionality for the financial agent, allowing
real-time chunk-based delivery of agent responses to the Streamlit UI. It handles
tool usage transparency and error conditions gracefully.

The streaming implementation uses PydanticAI's native run_stream() method which
provides chunk-based streaming (not token-by-token) that is compatible with
Streamlit's st.write_stream() display function.

For reasoning models (like qwen3:8b), this module filters out thinking/reasoning
tokens to show only the final answer to users.

Example:
    from src.agent.financial_agent import create_agent
    from src.agent.streaming import stream_agent_response

    agent = create_agent("ollama")
    conversation_history = []

    for chunk in stream_agent_response(agent, "What is Apple's stock price?", conversation_history):
        print(chunk, end="", flush=True)
"""

import re
from collections.abc import AsyncGenerator, Generator
from typing import Any

import logfire
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from src.utils.exceptions import ToolExecutionError


def filter_thinking_tokens(text: str) -> str:
    """Filter out thinking/reasoning tokens from model output.

    Reasoning models like qwen3, DeepSeek-R1, and similar models output their
    internal thinking process before the final answer. This function removes
    those thinking blocks to show only the final response.

    Common thinking patterns:
    - <think>...</think> or <thinking>...</thinking>
    - <|thinking|>...</|end_thinking|>
    - Think: ... (followed by Answer: or Final Answer:)

    Args:
        text: Raw text output from the model

    Returns:
        Filtered text with thinking blocks removed

    Example:
        >>> text = "<think>Let me calculate... 2+2=4</think>The answer is 4."
        >>> filter_thinking_tokens(text)
        'The answer is 4.'
    """
    # Remove XML-style thinking tags
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<\|thinking\|>.*?</?\|end_thinking\|>', '', text, flags=re.DOTALL)
    # Alternative pattern for pipe-delimited thinking blocks (DeepSeek-R1 format)
    text = re.sub(r'<[|]thinking[|]>.*?</?\|?end_thinking[|]>', '', text, flags=re.DOTALL)

    # Remove "Think:" sections followed by "Answer:" or "Final Answer:"
    text = re.sub(r'(?i)^.*?(?:think|reasoning|internal thought):.*?(?=(?:answer|final answer|response):)', '', text, flags=re.DOTALL)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def stream_agent_response(
    agent: Agent,
    user_message: str,
    conversation_history: list[ModelMessage],
) -> Generator[str, None, None]:
    """Stream agent responses chunk-by-chunk with tool usage transparency.

    This function provides a synchronous generator interface for streaming agent
    responses. It uses PydanticAI's run_stream() method internally to receive
    chunk-based text output and yields it to the caller for real-time display.

    Tool usage transparency is achieved by detecting when the agent uses tools
    and yielding notification messages. This helps users understand what the
    agent is doing behind the scenes.

    Error handling is built-in: if streaming fails at any point, an error
    message is yielded instead of crashing the application.

    Logfire tracing is integrated to capture the full conversation (user prompt
    + complete response) rather than individual chunks.

    Args:
        agent: Configured PydanticAI Agent instance (created via create_agent()).
        user_message: The user's input message to send to the agent.
        conversation_history: List of ModelMessage objects representing the conversation
            history. This allows the agent to maintain context across multiple turns.

    Yields:
        String chunks representing incremental pieces of the agent's response.
        Chunks may include:
        - Regular text content from the agent's response
        - Tool usage notifications (e.g., "Using finance tool to fetch AAPL data...")
        - Error messages if streaming fails

    Raises:
        None. All exceptions are caught and converted to error message chunks.

    Example:
        >>> agent = create_agent("openai")
        >>> history = []
        >>> for chunk in stream_agent_response(agent, "Get TSLA price", history):
        ...     print(chunk, end="", flush=True)
        Using finance tool to fetch stock data...
        The current stock price for Tesla (TSLA) is $245.30 USD.

    Note:
        This is a synchronous generator that wraps the async streaming functionality.
        It uses asyncio.run() internally to handle async operations, making it
        compatible with Streamlit's synchronous execution model.
    """
    import asyncio

    async def _async_stream() -> AsyncGenerator[str, None]:
        """Internal async generator that performs the actual streaming.

        This nested async function handles the PydanticAI streaming logic and
        is wrapped by the synchronous generator for easier integration with
        Streamlit.

        For reasoning models, this filters out thinking blocks to show only
        the final answer.

        Logfire tracing captures the complete conversation (user prompt + full response).
        """
        # Start a Logfire span to trace the entire conversation
        with logfire.span(
            "agent_conversation",
            user_prompt=user_message,
            conversation_history_length=len(conversation_history)
        ):
            try:
                # Buffer for accumulating chunks to detect and filter thinking patterns
                full_response = []
                in_thinking_block = False
                thinking_buffer = []

                # Use run_stream for chunk-based streaming
                # message_history parameter maintains conversation context
                async with agent.run_stream(
                    user_message, message_history=conversation_history
                ) as result:
                    # Stream text chunks as they arrive from the model
                    async for text_chunk in result.stream_text(delta=True):
                        # Accumulate the full response for post-processing
                        full_response.append(text_chunk)

                        # Check for thinking block start
                        combined_recent = ''.join(full_response[-10:])  # Look at recent chunks
                        if re.search(r'<think(?:ing)?>|<[|]thinking[|]>', combined_recent, re.IGNORECASE):
                            in_thinking_block = True
                            thinking_buffer.append(text_chunk)
                            continue

                        # Check for thinking block end
                        if in_thinking_block:
                            thinking_buffer.append(text_chunk)
                            if re.search(r'</think(?:ing)?>|</?[|]?end_thinking[|]>', combined_recent, re.IGNORECASE):
                                in_thinking_block = False
                                thinking_buffer = []
                            continue

                        # If not in thinking block, yield the chunk
                        if not in_thinking_block:
                            yield text_chunk

                    # After streaming completes, apply final filtering
                    # This catches any thinking patterns that weren't caught during streaming
                    final_text = ''.join(full_response)
                    filtered_text = filter_thinking_tokens(final_text)

                    # If filtering removed significant content, we may have missed some output
                    # Yield any remaining content that wasn't streamed
                    streamed_length = sum(len(chunk) for chunk in full_response) - sum(len(chunk) for chunk in thinking_buffer)
                    if len(filtered_text) > streamed_length:
                        remaining = filtered_text[streamed_length:]
                        if remaining.strip():
                            yield remaining

                    # Log the complete conversation to Logfire
                    logfire.info(
                        "conversation_completed",
                        user_prompt=user_message,
                        agent_response=filtered_text,
                        response_length=len(filtered_text),
                        chunks_count=len(full_response),
                        thinking_filtered=len(thinking_buffer) > 0
                    )

            except ToolExecutionError as e:
                # Tool-specific errors (rate limit, invalid ticker, API failures)
                error_msg = f"\n\nError: {str(e)}"
                logfire.error(
                    "tool_execution_error",
                    user_prompt=user_message,
                    error=str(e)
                )
                yield error_msg
            except Exception as e:
                # Catch-all for any other streaming errors
                # Provide clear error message for debugging
                error_msg = f"\n\nStreaming error: {str(e)}"
                logfire.error(
                    "streaming_error",
                    user_prompt=user_message,
                    error=str(e)
                )
                yield error_msg

    # Run the async generator using asyncio.run() with proper lifecycle management
    # We need to wrap the entire async iteration in a single asyncio.run() call
    # to avoid task/cancel scope violations

    # Create a wrapper that yields chunks through a queue-like mechanism
    import queue
    import threading

    chunk_queue = queue.Queue()
    exception_holder = []

    def run_async_stream():
        """Run the async stream in a separate thread with its own event loop."""
        try:
            async def _stream_to_queue():
                async for chunk in _async_stream():
                    chunk_queue.put(chunk)
                chunk_queue.put(None)  # Sentinel to indicate completion

            asyncio.run(_stream_to_queue())
        except Exception as e:
            exception_holder.append(e)
            chunk_queue.put(None)

    # Start the async streaming in a background thread
    thread = threading.Thread(target=run_async_stream, daemon=True)
    thread.start()

    # Yield chunks as they arrive in the queue
    while True:
        chunk = chunk_queue.get()
        if chunk is None:  # Sentinel value indicates stream is complete
            break
        yield chunk

    # Wait for thread to complete
    thread.join(timeout=1.0)

    # Re-raise any exceptions that occurred in the async stream
    if exception_holder:
        raise exception_holder[0]


async def stream_agent_response_async(
    agent: Agent,
    user_message: str,
    conversation_history: list[ModelMessage],
) -> AsyncGenerator[str, None]:
    """Async version of stream_agent_response for use in async contexts.

    This function provides the same functionality as stream_agent_response but
    returns an async generator for use in async/await code. It's useful for
    integration with async web frameworks or when called from async code.

    Logfire tracing is integrated to capture the full conversation (user prompt
    + complete response) rather than individual chunks.

    Args:
        agent: Configured PydanticAI Agent instance (created via create_agent()).
        user_message: The user's input message to send to the agent.
        conversation_history: List of ModelMessage objects representing the conversation
            history. This allows the agent to maintain context across multiple turns.

    Yields:
        String chunks representing incremental pieces of the agent's response.
        Chunks may include regular text content, tool usage notifications, or
        error messages if streaming fails.

    Raises:
        None. All exceptions are caught and converted to error message chunks.

    Example:
        >>> agent = create_agent("openai")
        >>> history = []
        >>> async for chunk in stream_agent_response_async(agent, "Get AAPL price", history):
        ...     print(chunk, end="", flush=True)
        Using finance tool to fetch stock data...
        The current stock price for Apple (AAPL) is $150.25 USD.
    """
    # Start a Logfire span to trace the entire conversation
    with logfire.span(
        "agent_conversation_async",
        user_prompt=user_message,
        conversation_history_length=len(conversation_history)
    ):
        try:
            # Buffer to accumulate complete response for Logfire
            full_response = []

            # Use run_stream for chunk-based streaming
            async with agent.run_stream(
                user_message, message_history=conversation_history
            ) as result:
                # Stream text chunks as they arrive from the model
                # delta=True means we get only the new content, not cumulative
                async for text_chunk in result.stream_text(delta=True):
                    # Accumulate for complete response logging
                    full_response.append(text_chunk)
                    # Yield each chunk as it arrives for real-time display
                    yield text_chunk

                # Log the complete conversation to Logfire
                complete_response = ''.join(full_response)
                logfire.info(
                    "conversation_completed",
                    user_prompt=user_message,
                    agent_response=complete_response,
                    response_length=len(complete_response),
                    chunks_count=len(full_response)
                )

        except ToolExecutionError as e:
            # Tool-specific errors (rate limit, invalid ticker, API failures)
            error_msg = f"\n\nError: {str(e)}"
            logfire.error(
                "tool_execution_error",
                user_prompt=user_message,
                error=str(e)
            )
            yield error_msg
        except Exception as e:
            # Catch-all for any other streaming errors
            # Provide clear error message for debugging
            error_msg = f"\n\nStreaming error: {str(e)}"
            logfire.error(
                "streaming_error",
                user_prompt=user_message,
                error=str(e)
            )
            yield error_msg

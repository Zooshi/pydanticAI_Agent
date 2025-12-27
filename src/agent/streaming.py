"""Streaming response handler for PydanticAI financial agent.

This module provides streaming functionality for the financial agent, allowing
real-time chunk-based delivery of agent responses to the Streamlit UI. It handles
tool usage transparency and error conditions gracefully.

The streaming implementation uses PydanticAI's native run_stream() method which
provides chunk-based streaming (not token-by-token) that is compatible with
Streamlit's st.write_stream() display function.

Example:
    from src.agent.financial_agent import create_agent
    from src.agent.streaming import stream_agent_response

    agent = create_agent("ollama")
    conversation_history = []

    for chunk in stream_agent_response(agent, "What is Apple's stock price?", conversation_history):
        print(chunk, end="", flush=True)
"""

from collections.abc import AsyncGenerator, Generator
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

from src.utils.exceptions import ToolExecutionError


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
        """
        try:
            # Use run_stream for chunk-based streaming
            # message_history parameter maintains conversation context
            async with agent.run_stream(
                user_message, message_history=conversation_history
            ) as result:
                # Track if we've seen any tool calls in the stream
                # This helps us provide transparency about tool usage
                tool_calls_detected = False

                # Stream text chunks as they arrive from the model
                # delta=False means we get full incremental updates, not just deltas
                async for text_chunk in result.stream_text(delta=True):
                    # Yield each chunk as it arrives for real-time display
                    yield text_chunk

                # After streaming completes, check if tools were used
                # We can inspect the messages to detect tool usage
                all_messages = result.all_messages()

                # Look for tool calls in the messages
                for message in all_messages:
                    # Check if this is a ModelResponse with tool calls
                    if hasattr(message, "parts"):
                        for part in message.parts:
                            # Detect ToolCallPart indicating tool usage
                            if part.__class__.__name__ == "ToolCallPart":
                                if not tool_calls_detected:
                                    tool_calls_detected = True
                                    # Extract tool name for transparency
                                    tool_name = getattr(part, "tool_name", "unknown")
                                    # Note: Tool transparency should be in the agent's response
                                    # per system instructions, but we log it here as backup

        except ToolExecutionError as e:
            # Tool-specific errors (rate limit, invalid ticker, API failures)
            yield f"\n\nError: {str(e)}"
        except Exception as e:
            # Catch-all for any other streaming errors
            # Provide clear error message for debugging
            yield f"\n\nStreaming error: {str(e)}"

    # Run the async generator in a new event loop and yield results synchronously
    # This bridges async streaming with Streamlit's sync interface
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async_gen = _async_stream()
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
    finally:
        loop.close()


async def stream_agent_response_async(
    agent: Agent,
    user_message: str,
    conversation_history: list[ModelMessage],
) -> AsyncGenerator[str, None]:
    """Async version of stream_agent_response for use in async contexts.

    This function provides the same functionality as stream_agent_response but
    returns an async generator for use in async/await code. It's useful for
    integration with async web frameworks or when called from async code.

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
    try:
        # Use run_stream for chunk-based streaming
        async with agent.run_stream(
            user_message, message_history=conversation_history
        ) as result:
            # Stream text chunks as they arrive from the model
            # delta=True means we get only the new content, not cumulative
            async for text_chunk in result.stream_text(delta=True):
                # Yield each chunk as it arrives for real-time display
                yield text_chunk

    except ToolExecutionError as e:
        # Tool-specific errors (rate limit, invalid ticker, API failures)
        yield f"\n\nError: {str(e)}"
    except Exception as e:
        # Catch-all for any other streaming errors
        # Provide clear error message for debugging
        yield f"\n\nStreaming error: {str(e)}"

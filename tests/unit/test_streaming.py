"""Unit tests for streaming response handler.

This module tests the streaming functionality for the PydanticAI financial agent,
ensuring that chunk-based streaming works correctly with proper tool transparency
and error handling.
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from src.agent.streaming import (
    filter_thinking_tokens,
    stream_agent_response,
    stream_agent_response_async,
)
from src.utils.exceptions import ToolExecutionError


class TestStreamAgentResponse:
    """Test suite for stream_agent_response synchronous generator."""

    def test_stream_agent_response_basic_text(self):
        """Test streaming basic text response without tool usage."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        # Mock stream_text to yield text chunks
        async def mock_stream_text(delta=True):
            chunks = ["Hello ", "world", "!"]
            for chunk in chunks:
                yield chunk

        mock_result.stream_text = mock_stream_text
        mock_result.all_messages = Mock(return_value=[])

        # Create async context manager for run_stream
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        conversation_history = []
        chunks = list(
            stream_agent_response(agent, "Test message", conversation_history)
        )

        # Verify chunks
        assert chunks == ["Hello ", "world", "!"]

        # Verify agent.run_stream was called with correct parameters
        agent.run_stream.assert_called_once_with(
            "Test message", message_history=conversation_history
        )

    def test_stream_agent_response_with_conversation_history(self):
        """Test streaming with existing conversation history."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            yield "Response text"

        mock_result.stream_text = mock_stream_text
        mock_result.all_messages = Mock(return_value=[])

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Create conversation history
        conversation_history = [
            ModelRequest(
                parts=[
                    SystemPromptPart(content="System prompt"),
                    UserPromptPart(content="Previous question"),
                ]
            ),
            ModelResponse(parts=[TextPart(content="Previous answer")]),
        ]

        # Execute streaming
        chunks = list(
            stream_agent_response(agent, "Follow-up question", conversation_history)
        )

        # Verify chunks
        assert chunks == ["Response text"]

        # Verify conversation history was passed
        agent.run_stream.assert_called_once_with(
            "Follow-up question", message_history=conversation_history
        )

    def test_stream_agent_response_empty_response(self):
        """Test handling of empty streaming response."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result with no chunks
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            # Yield nothing - empty generator
            return
            yield  # Make it a generator

        mock_result.stream_text = mock_stream_text
        mock_result.all_messages = Mock(return_value=[])

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Empty test", []))

        # Verify no chunks returned
        assert chunks == []

    def test_stream_agent_response_tool_execution_error(self):
        """Test handling of ToolExecutionError during streaming."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result that raises ToolExecutionError
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            raise ToolExecutionError("Rate limit exceeded for ticker AAPL")
            yield  # Make it a generator

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Get AAPL price", []))

        # Verify error message is yielded
        assert len(chunks) == 1
        assert "Error: Rate limit exceeded for ticker AAPL" in chunks[0]

    def test_stream_agent_response_generic_exception(self):
        """Test handling of generic exceptions during streaming."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result that raises generic exception
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            raise ValueError("Unexpected API error")
            yield  # Make it a generator

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Test query", []))

        # Verify error message is yielded
        assert len(chunks) == 1
        assert "Streaming error: Unexpected API error" in chunks[0]

    def test_stream_agent_response_with_tool_calls(self):
        """Test streaming response that includes tool calls."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            chunks = ["Using finance tool... ", "The price is $150.25"]
            for chunk in chunks:
                yield chunk

        mock_result.stream_text = mock_stream_text

        # Create messages with tool call
        mock_tool_call = Mock(spec=ToolCallPart)
        mock_tool_call.__class__.__name__ = "ToolCallPart"
        mock_tool_call.tool_name = "finance_tool"
        mock_tool_call.args = {"ticker": "AAPL"}

        mock_response = Mock(spec=ModelResponse)
        mock_response.parts = [mock_tool_call]

        mock_result.all_messages = Mock(return_value=[mock_response])

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Get AAPL price", []))

        # Verify chunks include tool transparency
        assert chunks == ["Using finance tool... ", "The price is $150.25"]

    def test_stream_agent_response_multiple_chunks(self):
        """Test streaming with multiple text chunks."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            chunks = ["The ", "current ", "stock ", "price ", "is ", "$150.25"]
            for chunk in chunks:
                yield chunk

        mock_result.stream_text = mock_stream_text
        mock_result.all_messages = Mock(return_value=[])

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Get price", []))

        # Verify all chunks received
        assert len(chunks) == 6
        assert "".join(chunks) == "The current stock price is $150.25"


class TestStreamAgentResponseAsync:
    """Test suite for stream_agent_response_async async generator."""

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_basic_text(self):
        """Test async streaming basic text response without tool usage."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        # Mock stream_text to yield text chunks
        async def mock_stream_text(delta=True):
            chunks = ["Async ", "streaming ", "works"]
            for chunk in chunks:
                yield chunk

        mock_result.stream_text = mock_stream_text

        # Create async context manager for run_stream
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        conversation_history = []
        chunks = []
        async for chunk in stream_agent_response_async(
            agent, "Test message", conversation_history
        ):
            chunks.append(chunk)

        # Verify chunks
        assert chunks == ["Async ", "streaming ", "works"]

        # Verify agent.run_stream was called with correct parameters
        agent.run_stream.assert_called_once_with(
            "Test message", message_history=conversation_history
        )

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_with_history(self):
        """Test async streaming with conversation history."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            yield "Follow-up response"

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Create conversation history
        conversation_history = [
            ModelRequest(
                parts=[UserPromptPart(content="Previous question")]
            ),
        ]

        # Execute streaming
        chunks = []
        async for chunk in stream_agent_response_async(
            agent, "Follow-up", conversation_history
        ):
            chunks.append(chunk)

        # Verify chunks
        assert chunks == ["Follow-up response"]

        # Verify history was passed
        agent.run_stream.assert_called_once_with(
            "Follow-up", message_history=conversation_history
        )

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_empty_response(self):
        """Test async handling of empty streaming response."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result with no chunks
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            # Yield nothing
            return
            yield  # Make it a generator

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = []
        async for chunk in stream_agent_response_async(agent, "Empty test", []):
            chunks.append(chunk)

        # Verify no chunks returned
        assert chunks == []

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_tool_execution_error(self):
        """Test async handling of ToolExecutionError during streaming."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result that raises ToolExecutionError
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            raise ToolExecutionError("Invalid ticker symbol: XYZ")
            yield  # Make it a generator

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = []
        async for chunk in stream_agent_response_async(agent, "Get XYZ price", []):
            chunks.append(chunk)

        # Verify error message is yielded
        assert len(chunks) == 1
        assert "Error: Invalid ticker symbol: XYZ" in chunks[0]

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_generic_exception(self):
        """Test async handling of generic exceptions during streaming."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result that raises generic exception
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            raise RuntimeError("Network timeout")
            yield  # Make it a generator

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = []
        async for chunk in stream_agent_response_async(agent, "Test query", []):
            chunks.append(chunk)

        # Verify error message is yielded
        assert len(chunks) == 1
        assert "Streaming error: Network timeout" in chunks[0]

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_multiple_chunks(self):
        """Test async streaming with multiple text chunks."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            chunks = ["I'm ", "using ", "the ", "research ", "tool ", "now."]
            for chunk in chunks:
                yield chunk

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = []
        async for chunk in stream_agent_response_async(agent, "Research Tesla", []):
            chunks.append(chunk)

        # Verify all chunks received
        assert len(chunks) == 6
        assert "".join(chunks) == "I'm using the research tool now."

    @pytest.mark.asyncio
    async def test_stream_agent_response_async_delta_parameter(self):
        """Test that delta=True is passed to stream_text."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        # Track the delta parameter
        delta_param_used = None

        async def mock_stream_text(delta=True):
            nonlocal delta_param_used
            delta_param_used = delta
            yield "Test"

        mock_result.stream_text = mock_stream_text

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = []
        async for chunk in stream_agent_response_async(agent, "Test", []):
            chunks.append(chunk)

        # Verify delta=True was used
        assert delta_param_used is True


class TestStreamingIntegration:
    """Integration tests for streaming functionality."""

    def test_stream_response_yields_in_order(self):
        """Test that chunks are yielded in the correct order."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            for i in range(10):
                yield f"Chunk {i} "

        mock_result.stream_text = mock_stream_text
        mock_result.all_messages = Mock(return_value=[])

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Test", []))

        # Verify order
        assert len(chunks) == 10
        for i, chunk in enumerate(chunks):
            assert chunk == f"Chunk {i} "

    def test_stream_response_handles_unicode_text(self):
        """Test streaming with Unicode text (but avoiding emojis for Windows)."""
        # Create mock agent
        agent = Mock(spec=Agent)

        # Create mock streaming result
        mock_result = AsyncMock()

        async def mock_stream_text(delta=True):
            # Use Unicode characters that are Windows-safe
            chunks = ["Price: ", "$150.25 ", "(USD)"]
            for chunk in chunks:
                yield chunk

        mock_result.stream_text = mock_stream_text
        mock_result.all_messages = Mock(return_value=[])

        # Create async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_result
        mock_context.__aexit__.return_value = None
        agent.run_stream = Mock(return_value=mock_context)

        # Execute streaming
        chunks = list(stream_agent_response(agent, "Test", []))

        # Verify Unicode handling
        assert chunks == ["Price: ", "$150.25 ", "(USD)"]
        assert "".join(chunks) == "Price: $150.25 (USD)"


class TestFilterThinkingTokens:
    """Test suite for filter_thinking_tokens function for reasoning models."""

    def test_filter_xml_think_tags(self):
        """Test filtering of <think>...</think> XML-style tags."""
        text = "<think>Let me calculate 2+2... equals 4</think>The answer is 4."
        result = filter_thinking_tokens(text)
        assert result == "The answer is 4."

    def test_filter_xml_thinking_tags(self):
        """Test filtering of <thinking>...</thinking> XML-style tags."""
        text = "<thinking>I need to analyze this question carefully...</thinking>Here is my response."
        result = filter_thinking_tokens(text)
        assert result == "Here is my response."

    def test_filter_pipe_thinking_tags(self):
        """Test filtering of <|thinking|>...<|end_thinking|> format."""
        text = "<|thinking|>Processing the request step by step<|end_thinking|>Final answer here."
        result = filter_thinking_tokens(text)
        assert result == "Final answer here."

    def test_filter_multiple_thinking_blocks(self):
        """Test filtering multiple thinking blocks in the same text."""
        text = (
            "<think>First thought</think>Some text<thinking>Second thought</thinking>More text"
        )
        result = filter_thinking_tokens(text)
        assert result == "Some textMore text"

    def test_filter_nested_thinking_content(self):
        """Test filtering thinking blocks with nested/complex content."""
        text = (
            "<think>Let me think:\n1. First step\n2. Second step\n3. Conclusion</think>"
            "The final answer is 42."
        )
        result = filter_thinking_tokens(text)
        assert result == "The final answer is 42."

    def test_filter_case_insensitive(self):
        """Test filtering is case-insensitive for think/thinking tags."""
        text = "<Think>Uppercase thinking</Think><THINKING>All caps</THINKING>Result"
        result = filter_thinking_tokens(text)
        assert result == "Result"

    def test_filter_think_colon_pattern(self):
        """Test filtering 'Think: ...' followed by 'Answer:' pattern."""
        text = (
            "Think: I need to calculate this carefully. Let me work through it step by step. "
            "Answer: The result is 10."
        )
        result = filter_thinking_tokens(text)
        # After filtering the "Think:" section, we should get the answer
        assert "The result is 10" in result
        assert "Think:" not in result or result.startswith("Answer:")

    def test_no_thinking_blocks_unchanged(self):
        """Test that text without thinking blocks remains unchanged."""
        text = "This is a normal response with no thinking blocks."
        result = filter_thinking_tokens(text)
        assert result == text

    def test_empty_string(self):
        """Test filtering empty string."""
        result = filter_thinking_tokens("")
        assert result == ""

    def test_only_thinking_blocks(self):
        """Test text with only thinking blocks returns empty string."""
        text = "<think>Only thinking here</think><thinking>More thinking</thinking>"
        result = filter_thinking_tokens(text)
        assert result == ""

    def test_whitespace_handling(self):
        """Test that leading/trailing whitespace is stripped."""
        text = "  <think>Thinking...</think>  Result with spaces  "
        result = filter_thinking_tokens(text)
        assert result == "Result with spaces"

    def test_multiline_thinking_blocks(self):
        """Test filtering multiline thinking blocks."""
        text = """<think>
Let me think about this:
- Point 1
- Point 2
- Conclusion
</think>
Final answer here."""
        result = filter_thinking_tokens(text)
        assert "Final answer here." in result
        assert "Point 1" not in result
        assert "Point 2" not in result

    def test_mixed_thinking_formats(self):
        """Test filtering mixed thinking block formats in one text."""
        text = (
            "<think>First format</think>"
            "Some text"
            "<|thinking|>Second format<|end_thinking|>"
            "More text"
            "<thinking>Third format</thinking>"
            "Final result"
        )
        result = filter_thinking_tokens(text)
        assert result == "Some textMore textFinal result"

    def test_reasoning_pattern(self):
        """Test filtering 'Reasoning:' followed by 'Answer:' pattern."""
        text = "Reasoning: Step by step analysis goes here. Answer: The answer is yes."
        result = filter_thinking_tokens(text)
        # The regex should remove the reasoning section
        assert "yes" in result

    def test_preserves_legitimate_content(self):
        """Test that legitimate content is preserved even with similar patterns."""
        # This should NOT be filtered (no closing tag)
        text = "Let's think about this problem. The solution is X."
        result = filter_thinking_tokens(text)
        # Since there's no actual thinking block, text should remain
        assert "Let's think about this problem" in result
        assert "The solution is X" in result

    def test_qwen3_realistic_output(self):
        """Test realistic qwen3:8b model output with thinking blocks."""
        # Simulated output from qwen3:8b reasoning model
        text = """<think>
The user is asking about Apple's stock price. I need to:
1. Convert "Apple" to ticker symbol "AAPL"
2. Use the finance tool to fetch the data
3. Format the response clearly
</think>I'm using the finance tool to fetch the latest stock price for AAPL...

The current stock price of Apple (AAPL) is $150.25 USD."""

        result = filter_thinking_tokens(text)

        # Verify thinking block is removed
        assert "Convert" not in result
        assert "ticker symbol" not in result

        # Verify actual response is preserved
        assert "using the finance tool" in result
        assert "$150.25" in result
        assert "AAPL" in result

    def test_deepseek_r1_format(self):
        """Test DeepSeek-R1 style thinking format."""
        text = "<|thinking|>Let me analyze this query...</|end_thinking|>Here is the answer."
        result = filter_thinking_tokens(text)
        assert result == "Here is the answer."
        assert "analyze" not in result

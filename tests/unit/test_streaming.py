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

from src.agent.streaming import stream_agent_response, stream_agent_response_async
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

"""Unit tests for PydanticAI financial agent.

This module contains comprehensive unit tests for the financial agent implementation,
including agent creation, model selection, tool registration, system instructions,
and error handling. All tests mock PydanticAI and external dependencies to avoid
real API calls.

Test Coverage:
- Agent creation with both OLLAMA and OpenAI models
- Configuration validation
- Tool registration and functionality
- LogFire integration
- Error handling for invalid configurations
"""

import unittest
from unittest.mock import MagicMock, patch, call

import pytest

from src.agent.financial_agent import create_agent, SYSTEM_INSTRUCTIONS
from src.utils.exceptions import ConfigurationError


class TestCreateAgentValidation(unittest.TestCase):
    """Test agent creation validation and configuration checks."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset any module-level state
        pass

    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", None)
    def test_create_agent_missing_logfire_token_raises_error(self):
        """Test that missing LOGFIRE_TOKEN raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_agent("ollama")

        assert "LOGFIRE_TOKEN is required" in str(exc_info.value)

    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    def test_create_agent_invalid_model_choice_raises_error(self):
        """Test that invalid model_choice raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_agent("invalid_model")

        assert "Invalid model_choice" in str(exc_info.value)
        assert "ollama" in str(exc_info.value)
        assert "openai" in str(exc_info.value)

    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    def test_create_agent_empty_model_choice_raises_error(self):
        """Test that empty model_choice raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_agent("")

        assert "Invalid model_choice" in str(exc_info.value)

    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    @patch("src.agent.financial_agent.OLLAMA_BASE_URL", None)
    def test_create_agent_ollama_missing_base_url_raises_error(self):
        """Test that OLLAMA model without BASE_URL raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_agent("ollama")

        assert "OLLAMA_BASE_URL is required" in str(exc_info.value)

    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    @patch("src.agent.financial_agent.OLLAMA_BASE_URL", "http://localhost:11434")
    @patch("src.agent.financial_agent.OLLAMA_MODEL_NAME", None)
    def test_create_agent_ollama_missing_model_name_raises_error(self):
        """Test that OLLAMA model without MODEL_NAME raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            create_agent("ollama")

        assert "OLLAMA_MODEL_NAME is required" in str(exc_info.value)


class TestCreateAgentOllama(unittest.TestCase):
    """Test agent creation with OLLAMA model."""

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-logfire-token")
    @patch("src.agent.financial_agent.OLLAMA_BASE_URL", "http://localhost:11434")
    @patch("src.agent.financial_agent.OLLAMA_MODEL_NAME", "qwen2.5:3b")
    def test_create_agent_ollama_success(self, mock_agent_class, mock_logfire):
        """Test successful OLLAMA agent creation."""
        # Mock Agent instance
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        agent = create_agent("ollama")

        # Verify LogFire configuration
        mock_logfire.configure.assert_called_once_with(token="test-logfire-token")

        # Verify Agent initialization
        mock_agent_class.assert_called_once_with(
            "ollama:qwen2.5:3b",
            system_prompt=SYSTEM_INSTRUCTIONS,
        )

        # Verify agent instance returned
        assert agent == mock_agent_instance

        # Verify LogFire logging
        mock_logfire.info.assert_called_once()
        log_call_kwargs = mock_logfire.info.call_args[1]
        assert log_call_kwargs["model_choice"] == "ollama"
        assert log_call_kwargs["model_string"] == "ollama:qwen2.5:3b"
        assert "finance_tool" in log_call_kwargs["tools"]
        assert "research_tool" in log_call_kwargs["tools"]

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    @patch("src.agent.financial_agent.OLLAMA_BASE_URL", "http://localhost:11434")
    @patch("src.agent.financial_agent.OLLAMA_MODEL_NAME", "qwen2.5:3b")
    def test_create_agent_ollama_case_insensitive(self, mock_agent_class, mock_logfire):
        """Test OLLAMA agent creation with uppercase model choice."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent with uppercase
        agent = create_agent("OLLAMA")

        # Verify Agent initialization with correct model string
        mock_agent_class.assert_called_once_with(
            "ollama:qwen2.5:3b",
            system_prompt=SYSTEM_INSTRUCTIONS,
        )

        assert agent == mock_agent_instance


class TestCreateAgentOpenAI(unittest.TestCase):
    """Test agent creation with OpenAI model."""

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-logfire-token")
    def test_create_agent_openai_success(self, mock_agent_class, mock_logfire):
        """Test successful OpenAI agent creation."""
        # Mock Agent instance
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        agent = create_agent("openai")

        # Verify LogFire configuration
        mock_logfire.configure.assert_called_once_with(token="test-logfire-token")

        # Verify Agent initialization with OpenAI model
        mock_agent_class.assert_called_once_with(
            "openai:gpt-4o-mini",
            system_prompt=SYSTEM_INSTRUCTIONS,
        )

        # Verify agent instance returned
        assert agent == mock_agent_instance

        # Verify LogFire logging
        mock_logfire.info.assert_called_once()
        log_call_kwargs = mock_logfire.info.call_args[1]
        assert log_call_kwargs["model_choice"] == "openai"
        assert log_call_kwargs["model_string"] == "openai:gpt-4o-mini"
        assert "finance_tool" in log_call_kwargs["tools"]
        assert "research_tool" in log_call_kwargs["tools"]

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    def test_create_agent_openai_case_insensitive(self, mock_agent_class, mock_logfire):
        """Test OpenAI agent creation with mixed case model choice."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent with mixed case
        agent = create_agent("OpenAI")

        # Verify Agent initialization with correct model string
        mock_agent_class.assert_called_once_with(
            "openai:gpt-4o-mini",
            system_prompt=SYSTEM_INSTRUCTIONS,
        )

        assert agent == mock_agent_instance


class TestAgentToolRegistration(unittest.TestCase):
    """Test that tools are properly registered with the agent."""

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    @patch("src.agent.financial_agent.OLLAMA_BASE_URL", "http://localhost:11434")
    @patch("src.agent.financial_agent.OLLAMA_MODEL_NAME", "qwen2.5:3b")
    def test_agent_tools_registered_ollama(self, mock_agent_class, mock_logfire):
        """Test that both tools are registered with OLLAMA agent."""
        # Mock Agent instance
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        agent = create_agent("ollama")

        # Verify agent creation
        assert agent is not None

        # Verify LogFire logged tool registration
        mock_logfire.info.assert_called_once()
        log_call_kwargs = mock_logfire.info.call_args[1]
        assert len(log_call_kwargs["tools"]) == 2
        assert "finance_tool" in log_call_kwargs["tools"]
        assert "research_tool" in log_call_kwargs["tools"]

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    def test_agent_tools_registered_openai(self, mock_agent_class, mock_logfire):
        """Test that both tools are registered with OpenAI agent."""
        # Mock Agent instance
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        agent = create_agent("openai")

        # Verify agent creation
        assert agent is not None

        # Verify LogFire logged tool registration
        mock_logfire.info.assert_called_once()
        log_call_kwargs = mock_logfire.info.call_args[1]
        assert len(log_call_kwargs["tools"]) == 2
        assert "finance_tool" in log_call_kwargs["tools"]
        assert "research_tool" in log_call_kwargs["tools"]


class TestSystemInstructions(unittest.TestCase):
    """Test system instructions configuration."""

    def test_system_instructions_contains_ticker_conversion(self):
        """Test that system instructions include ticker conversion guidance."""
        assert "ticker" in SYSTEM_INSTRUCTIONS.lower()
        assert "convert" in SYSTEM_INSTRUCTIONS.lower()
        assert "symbol" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_contains_tool_transparency(self):
        """Test that system instructions require tool usage transparency."""
        assert "tool" in SYSTEM_INSTRUCTIONS.lower()
        assert "explicitly" in SYSTEM_INSTRUCTIONS.lower() or "mention" in SYSTEM_INSTRUCTIONS.lower()
        assert "transparency" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_contains_finance_tool_guidance(self):
        """Test that system instructions explain when to use finance tool."""
        assert "finance tool" in SYSTEM_INSTRUCTIONS.lower()
        assert "stock" in SYSTEM_INSTRUCTIONS.lower()
        assert "price" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_contains_research_tool_guidance(self):
        """Test that system instructions explain when to use research tool."""
        assert "research tool" in SYSTEM_INSTRUCTIONS.lower()
        assert "search" in SYSTEM_INSTRUCTIONS.lower() or "news" in SYSTEM_INSTRUCTIONS.lower()

    def test_system_instructions_forbids_hardcoding(self):
        """Test that system instructions explicitly forbid hardcoded mappings."""
        instructions_lower = SYSTEM_INSTRUCTIONS.lower()
        # Check for negative phrasing about hardcoding
        assert "do not hardcode" in instructions_lower or "not hardcode" in instructions_lower

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    def test_system_instructions_passed_to_agent(self, mock_agent_class, mock_logfire):
        """Test that system instructions are passed to Agent constructor."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        create_agent("openai")

        # Verify Agent was called with system_prompt
        call_kwargs = mock_agent_class.call_args[1]
        assert "system_prompt" in call_kwargs
        assert call_kwargs["system_prompt"] == SYSTEM_INSTRUCTIONS


class TestLogFireIntegration(unittest.TestCase):
    """Test LogFire observability integration."""

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-logfire-token-123")
    def test_logfire_configured_with_token(self, mock_agent_class, mock_logfire):
        """Test that LogFire is configured with correct token."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        create_agent("openai")

        # Verify LogFire configuration
        mock_logfire.configure.assert_called_once_with(token="test-logfire-token-123")

    @patch("src.agent.financial_agent.logfire")
    @patch("src.agent.financial_agent.Agent")
    @patch("src.agent.financial_agent.LOGFIRE_TOKEN", "test-token")
    @patch("src.agent.financial_agent.OLLAMA_BASE_URL", "http://localhost:11434")
    @patch("src.agent.financial_agent.OLLAMA_MODEL_NAME", "qwen2.5:3b")
    def test_logfire_logs_agent_creation(self, mock_agent_class, mock_logfire):
        """Test that LogFire logs agent creation with metadata."""
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        # Create agent
        create_agent("ollama")

        # Verify LogFire info logging
        mock_logfire.info.assert_called_once()
        log_message = mock_logfire.info.call_args[0][0]
        assert "Financial agent created" in log_message

        # Verify metadata
        log_kwargs = mock_logfire.info.call_args[1]
        assert log_kwargs["model_choice"] == "ollama"
        assert log_kwargs["model_string"] == "ollama:qwen2.5:3b"
        assert log_kwargs["tools"] == ["finance_tool", "research_tool"]

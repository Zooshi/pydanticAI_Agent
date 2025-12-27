"""Unit tests for custom exception classes.

Tests cover:
- Exception inheritance hierarchy
- Exception message preservation
- Exception instantiation
- Base exception catching
"""

import pytest

from src.utils.exceptions import (
    FinancialAgentError,
    ConfigurationError,
    RateLimitExceededError,
    ToolExecutionError,
)


class TestFinancialAgentError:
    """Tests for base FinancialAgentError exception."""

    def test_is_exception(self) -> None:
        """Test FinancialAgentError inherits from Exception."""
        error = FinancialAgentError("Test error")
        assert isinstance(error, Exception)

    def test_message_preservation(self) -> None:
        """Test FinancialAgentError preserves error message."""
        message = "Base error message"
        error = FinancialAgentError(message)
        assert str(error) == message

    def test_can_be_raised_and_caught(self) -> None:
        """Test FinancialAgentError can be raised and caught."""
        with pytest.raises(FinancialAgentError) as exc_info:
            raise FinancialAgentError("Test exception")

        assert str(exc_info.value) == "Test exception"

    def test_catches_all_custom_exceptions(self) -> None:
        """Test FinancialAgentError catches all derived exceptions."""
        # ConfigurationError should be catchable as FinancialAgentError
        with pytest.raises(FinancialAgentError):
            raise ConfigurationError("Config error")

        # RateLimitExceededError should be catchable as FinancialAgentError
        with pytest.raises(FinancialAgentError):
            raise RateLimitExceededError("Rate limit error")

        # ToolExecutionError should be catchable as FinancialAgentError
        with pytest.raises(FinancialAgentError):
            raise ToolExecutionError("Tool error")


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_is_financial_agent_error(self) -> None:
        """Test ConfigurationError inherits from FinancialAgentError."""
        error = ConfigurationError("Test error")
        assert isinstance(error, FinancialAgentError)

    def test_is_exception(self) -> None:
        """Test ConfigurationError inherits from Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)

    def test_message_preservation(self) -> None:
        """Test ConfigurationError preserves error message."""
        message = "Missing OPENAI_API_KEY environment variable"
        error = ConfigurationError(message)
        assert str(error) == message

    def test_can_be_raised_and_caught(self) -> None:
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Config validation failed")

        assert "Config validation failed" in str(exc_info.value)

    def test_multiline_message(self) -> None:
        """Test ConfigurationError handles multiline messages."""
        message = "TAVILY_API_KEY is required.\nPlease set it in your .env file."
        error = ConfigurationError(message)
        assert str(error) == message

    def test_empty_message(self) -> None:
        """Test ConfigurationError can be instantiated with empty message."""
        error = ConfigurationError()
        # Empty exception should have empty string representation
        assert str(error) == ""


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError exception."""

    def test_is_financial_agent_error(self) -> None:
        """Test RateLimitExceededError inherits from FinancialAgentError."""
        error = RateLimitExceededError("Test error")
        assert isinstance(error, FinancialAgentError)

    def test_is_exception(self) -> None:
        """Test RateLimitExceededError inherits from Exception."""
        error = RateLimitExceededError("Test error")
        assert isinstance(error, Exception)

    def test_message_preservation(self) -> None:
        """Test RateLimitExceededError preserves error message."""
        message = "Rate limit exceeded. Please wait 45.2 seconds."
        error = RateLimitExceededError(message)
        assert str(error) == message

    def test_can_be_raised_and_caught(self) -> None:
        """Test RateLimitExceededError can be raised and caught."""
        with pytest.raises(RateLimitExceededError) as exc_info:
            raise RateLimitExceededError("Too many requests")

        assert "Too many requests" in str(exc_info.value)

    def test_wait_time_message_format(self) -> None:
        """Test RateLimitExceededError with typical wait time message."""
        message = (
            "Rate limit exceeded. Maximum 10 requests per 60 seconds. "
            "Please wait 23.5 seconds before retrying."
        )
        error = RateLimitExceededError(message)
        assert "Rate limit exceeded" in str(error)
        assert "23.5 seconds" in str(error)


class TestToolExecutionError:
    """Tests for ToolExecutionError exception."""

    def test_is_financial_agent_error(self) -> None:
        """Test ToolExecutionError inherits from FinancialAgentError."""
        error = ToolExecutionError("Test error")
        assert isinstance(error, FinancialAgentError)

    def test_is_exception(self) -> None:
        """Test ToolExecutionError inherits from Exception."""
        error = ToolExecutionError("Test error")
        assert isinstance(error, Exception)

    def test_message_preservation(self) -> None:
        """Test ToolExecutionError preserves error message."""
        message = "YFinance API error for ticker 'AAPL': Connection timeout"
        error = ToolExecutionError(message)
        assert str(error) == message

    def test_can_be_raised_and_caught(self) -> None:
        """Test ToolExecutionError can be raised and caught."""
        with pytest.raises(ToolExecutionError) as exc_info:
            raise ToolExecutionError("Tool execution failed")

        assert "Tool execution failed" in str(exc_info.value)

    def test_finance_tool_error_format(self) -> None:
        """Test ToolExecutionError with finance tool error message."""
        message = "YFinance API error for ticker 'TSLA': Invalid ticker symbol"
        error = ToolExecutionError(message)
        assert "YFinance" in str(error)
        assert "TSLA" in str(error)
        assert "Invalid ticker symbol" in str(error)

    def test_research_tool_error_format(self) -> None:
        """Test ToolExecutionError with research tool error message."""
        message = "Tavily API error: Request timeout after 30 seconds"
        error = ToolExecutionError(message)
        assert "Tavily" in str(error)
        assert "timeout" in str(error)


class TestExceptionHierarchy:
    """Tests for exception hierarchy relationships."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test all custom exceptions inherit from FinancialAgentError."""
        exceptions = [
            ConfigurationError("test"),
            RateLimitExceededError("test"),
            ToolExecutionError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, FinancialAgentError)
            assert isinstance(exc, Exception)

    def test_specific_exception_catching(self) -> None:
        """Test that specific exceptions can be caught individually."""
        # Test ConfigurationError catching
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config error")

        # Test RateLimitExceededError catching
        with pytest.raises(RateLimitExceededError):
            raise RateLimitExceededError("Rate limit error")

        # Test ToolExecutionError catching
        with pytest.raises(ToolExecutionError):
            raise ToolExecutionError("Tool error")

    def test_base_exception_catches_all(self) -> None:
        """Test FinancialAgentError catches all derived exceptions."""
        exceptions_to_test = [
            ConfigurationError("Config"),
            RateLimitExceededError("Rate"),
            ToolExecutionError("Tool"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(FinancialAgentError):
                raise exc

    def test_exception_not_caught_by_sibling(self) -> None:
        """Test that exception types don't catch their siblings."""
        # ConfigurationError should not catch RateLimitExceededError
        with pytest.raises(RateLimitExceededError):
            try:
                raise RateLimitExceededError("Rate error")
            except ConfigurationError:
                pytest.fail("ConfigurationError should not catch RateLimitExceededError")

        # RateLimitExceededError should not catch ToolExecutionError
        with pytest.raises(ToolExecutionError):
            try:
                raise ToolExecutionError("Tool error")
            except RateLimitExceededError:
                pytest.fail("RateLimitExceededError should not catch ToolExecutionError")

        # ToolExecutionError should not catch ConfigurationError
        with pytest.raises(ConfigurationError):
            try:
                raise ConfigurationError("Config error")
            except ToolExecutionError:
                pytest.fail("ToolExecutionError should not catch ConfigurationError")


class TestExceptionUsagePatterns:
    """Tests for common exception usage patterns."""

    def test_exception_chaining(self) -> None:
        """Test exception chaining with raise from."""
        original_error = ValueError("Original error")

        with pytest.raises(ToolExecutionError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise ToolExecutionError("Tool failed") from e

        # Check the exception chain
        assert exc_info.value.__cause__ is original_error

    def test_multiple_exception_types_in_try_except(self) -> None:
        """Test catching multiple exception types."""
        def raise_config_error():
            raise ConfigurationError("Config error")

        def raise_rate_limit_error():
            raise RateLimitExceededError("Rate error")

        # Catch specific exceptions separately
        with pytest.raises(ConfigurationError):
            raise_config_error()

        with pytest.raises(RateLimitExceededError):
            raise_rate_limit_error()

        # Catch both with base exception
        errors_caught = []
        for func in [raise_config_error, raise_rate_limit_error]:
            try:
                func()
            except FinancialAgentError as e:
                errors_caught.append(type(e).__name__)

        assert "ConfigurationError" in errors_caught
        assert "RateLimitExceededError" in errors_caught

    def test_exception_with_formatted_message(self) -> None:
        """Test exceptions with formatted error messages."""
        ticker = "AAPL"
        error_detail = "Connection timeout"
        message = f"YFinance API error for ticker '{ticker}': {error_detail}"

        error = ToolExecutionError(message)
        assert ticker in str(error)
        assert error_detail in str(error)

"""Custom exception classes for PydanticAI Streamlit Financial Research Agent.

This module provides a centralized hierarchy of exception classes used throughout
the application. All custom exceptions inherit from a base FinancialAgentError
class for easy catching and error handling.

Exception Hierarchy:
    FinancialAgentError (base)
    ├── ConfigurationError - Missing or invalid configuration
    ├── RateLimitExceededError - Rate limit exceeded with wait time info
    └── ToolExecutionError - Tool execution failures

Example:
    from src.utils.exceptions import RateLimitExceededError, ToolExecutionError

    try:
        tool.execute()
    except RateLimitExceededError as e:
        print(f"Rate limited: {e}")
    except ToolExecutionError as e:
        print(f"Tool failed: {e}")
"""


class FinancialAgentError(Exception):
    """Base exception class for all custom Financial Agent errors.

    All custom exceptions in this application should inherit from this base
    class to allow for easier exception handling and categorization.
    """
    pass


class ConfigurationError(FinancialAgentError):
    """Raised when required configuration is missing or invalid.

    This exception is raised during application startup or configuration
    validation when required environment variables are missing, invalid,
    or incompatible with the selected model.

    Example:
        raise ConfigurationError("OPENAI_API_KEY is required for OpenAI model")
    """
    pass


class RateLimitExceededError(FinancialAgentError):
    """Raised when rate limit is exceeded.

    This exception is raised when a request would exceed the configured
    rate limit. The error message should include the wait time in seconds
    before the next request can be made.

    Example:
        raise RateLimitExceededError(
            "Rate limit exceeded. Please wait 45.2 seconds before retrying."
        )
    """
    pass


class ToolExecutionError(FinancialAgentError):
    """Raised when a tool fails to execute.

    This exception is raised when a tool (finance, research, etc.) encounters
    an error during execution. The error message should include context about
    which tool failed and why.

    Example:
        raise ToolExecutionError(
            "YFinance API error for ticker 'AAPL': Connection timeout"
        )
    """
    pass

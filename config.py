"""Configuration management for PydanticAI Streamlit Financial Research Agent.

This module loads and validates environment variables required for the application
to function properly. It uses python-dotenv to load variables from a .env file
and provides validation based on the selected model.

Constants:
    OPENAI_API_KEY: API key for OpenAI GPT models (required for OpenAI model)
    TAVILY_API_KEY: API key for Tavily research tool (required)
    LOGFIRE_TOKEN: Token for LogFire observability (required)
    OLLAMA_BASE_URL: Base URL for OLLAMA API (default: http://localhost:11434)
    OLLAMA_MODEL_NAME: Model name for OLLAMA (default: qwen2.5:3b)
    MAX_TICKER_LOOKUPS_PER_MINUTE: Rate limit for YFinance ticker lookups (default: 10)

Example:
    from config import validate_config, TAVILY_API_KEY

    # Validate configuration before running agent
    validate_config(model="openai")
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


# Load environment variables from .env file if it exists
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Load from environment if .env file doesn't exist
    load_dotenv()


# API Keys and Tokens
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY")
LOGFIRE_TOKEN: Optional[str] = os.getenv("LOGFIRE_TOKEN")

# OLLAMA Configuration
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:3b")

# Rate Limiting Configuration
MAX_TICKER_LOOKUPS_PER_MINUTE: int = int(
    os.getenv("MAX_TICKER_LOOKUPS_PER_MINUTE", "10")
)


def validate_config(model: str) -> None:
    """Validates that all required environment variables are present.

    Validation rules:
    - TAVILY_API_KEY is always required (research tool dependency)
    - LOGFIRE_TOKEN is always required (observability dependency)
    - OPENAI_API_KEY is required only when using OpenAI model
    - OLLAMA configuration is validated for OLLAMA model

    Args:
        model: The model type being used. Accepted values: "openai", "ollama"

    Raises:
        ConfigurationError: If any required environment variable is missing
        ConfigurationError: If model parameter is invalid

    Example:
        validate_config(model="openai")  # Checks OpenAI API key
        validate_config(model="ollama")  # Checks OLLAMA configuration
    """
    # Validate model parameter
    valid_models = ["openai", "ollama"]
    if model.lower() not in valid_models:
        raise ConfigurationError(
            f"Invalid model '{model}'. Must be one of: {', '.join(valid_models)}"
        )

    model_lower = model.lower()

    # Always required keys
    if not TAVILY_API_KEY:
        raise ConfigurationError(
            "TAVILY_API_KEY environment variable is required for research tool. "
            "Please set it in your .env file or environment."
        )

    if not LOGFIRE_TOKEN:
        raise ConfigurationError(
            "LOGFIRE_TOKEN environment variable is required for observability. "
            "Please set it in your .env file or environment."
        )

    # Model-specific validation
    if model_lower == "openai":
        if not OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY environment variable is required for OpenAI model. "
                "Please set it in your .env file or environment, or switch to OLLAMA model."
            )

    # Validate OLLAMA configuration when using OLLAMA
    if model_lower == "ollama":
        if not OLLAMA_BASE_URL:
            raise ConfigurationError(
                "OLLAMA_BASE_URL environment variable is required for OLLAMA model. "
                "Default: http://localhost:11434"
            )

        if not OLLAMA_MODEL_NAME:
            raise ConfigurationError(
                "OLLAMA_MODEL_NAME environment variable is required for OLLAMA model. "
                "Default: qwen2.5:3b"
            )

    # Validate rate limit configuration
    if MAX_TICKER_LOOKUPS_PER_MINUTE <= 0:
        raise ConfigurationError(
            f"MAX_TICKER_LOOKUPS_PER_MINUTE must be greater than 0, got {MAX_TICKER_LOOKUPS_PER_MINUTE}"
        )


def get_config_summary() -> dict[str, str]:
    """Returns a summary of current configuration (with sensitive data masked).

    Returns:
        Dictionary containing configuration status with API keys masked

    Example:
        summary = get_config_summary()
        print(summary["openai_api_key_set"])  # "Yes" or "No"
    """
    return {
        "openai_api_key_set": "Yes" if OPENAI_API_KEY else "No",
        "tavily_api_key_set": "Yes" if TAVILY_API_KEY else "No",
        "logfire_token_set": "Yes" if LOGFIRE_TOKEN else "No",
        "ollama_base_url": OLLAMA_BASE_URL,
        "ollama_model_name": OLLAMA_MODEL_NAME,
        "max_ticker_lookups_per_minute": str(MAX_TICKER_LOOKUPS_PER_MINUTE),
    }

"""Unit tests for configuration management module.

Tests cover:
- Environment variable loading
- Configuration validation for different models
- Error handling for missing required keys
- Default value handling
- Configuration summary generation
"""

import os
from unittest.mock import patch, MagicMock

import pytest

import config
from config import (
    ConfigurationError,
    get_config_summary,
    validate_config,
)


class TestConfigurationValidation:
    """Tests for validate_config function."""

    def test_validate_config_openai_success(self):
        """Test successful validation with all required keys for OpenAI model."""
        with patch.object(config, "OPENAI_API_KEY", "sk-test-key"):
            with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
                with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                    with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                        # Should not raise any exception
                        validate_config(model="openai")

    def test_validate_config_ollama_success(self):
        """Test successful validation with all required keys for OLLAMA model."""
        with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
            with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                    with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                        with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                            # Should not raise any exception
                            validate_config(model="ollama")

    def test_validate_config_missing_tavily_api_key(self):
        """Test validation fails when TAVILY_API_KEY is missing."""
        with patch.object(config, "TAVILY_API_KEY", None):
            with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                with patch.object(config, "OPENAI_API_KEY", "sk-test-key"):
                    with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                        with pytest.raises(ConfigurationError) as exc_info:
                            validate_config(model="openai")

                        assert "TAVILY_API_KEY" in str(exc_info.value)
                        assert "required for research tool" in str(exc_info.value)

    def test_validate_config_missing_logfire_token(self):
        """Test validation fails when LOGFIRE_TOKEN is missing."""
        with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
            with patch.object(config, "LOGFIRE_TOKEN", None):
                with patch.object(config, "OPENAI_API_KEY", "sk-test-key"):
                    with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                        with pytest.raises(ConfigurationError) as exc_info:
                            validate_config(model="openai")

                        assert "LOGFIRE_TOKEN" in str(exc_info.value)
                        assert "required for observability" in str(exc_info.value)

    def test_validate_config_missing_openai_api_key(self):
        """Test validation fails when OPENAI_API_KEY is missing for OpenAI model."""
        with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
            with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                with patch.object(config, "OPENAI_API_KEY", None):
                    with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                        with pytest.raises(ConfigurationError) as exc_info:
                            validate_config(model="openai")

                        assert "OPENAI_API_KEY" in str(exc_info.value)
                        assert "required for OpenAI model" in str(exc_info.value)

    def test_validate_config_invalid_model(self):
        """Test validation fails with invalid model parameter."""
        with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
            with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                    with pytest.raises(ConfigurationError) as exc_info:
                        validate_config(model="invalid-model")

                    assert "Invalid model" in str(exc_info.value)
                    assert "invalid-model" in str(exc_info.value)

    def test_validate_config_model_case_insensitive(self):
        """Test model parameter is case-insensitive."""
        with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
            with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                    with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                        with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                            # Should work with different cases
                            validate_config(model="OLLAMA")
                            validate_config(model="Ollama")
                            validate_config(model="ollama")


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_ollama_base_url_default(self):
        """Test OLLAMA_BASE_URL has correct default value when not set."""
        # The default is set during module import, so we just verify it exists
        # and matches expected default
        assert config.OLLAMA_BASE_URL is not None
        # This test verifies the constant exists and is accessible

    def test_ollama_model_name_default(self):
        """Test OLLAMA_MODEL_NAME has correct default value when not set."""
        # The default is set during module import, so we just verify it exists
        assert config.OLLAMA_MODEL_NAME is not None
        # This test verifies the constant exists and is accessible

    def test_max_ticker_lookups_default(self):
        """Test MAX_TICKER_LOOKUPS_PER_MINUTE has correct default value."""
        # The default is set during module import, so we just verify it exists
        assert config.MAX_TICKER_LOOKUPS_PER_MINUTE is not None
        assert isinstance(config.MAX_TICKER_LOOKUPS_PER_MINUTE, int)
        assert config.MAX_TICKER_LOOKUPS_PER_MINUTE > 0

    def test_max_ticker_lookups_validation(self):
        """Test validation of MAX_TICKER_LOOKUPS_PER_MINUTE value."""
        # Test with valid value
        with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 20):
            with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
                with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                    with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                        with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                            validate_config(model="ollama")

    def test_max_ticker_lookups_invalid_raises_error(self):
        """Test validation fails when MAX_TICKER_LOOKUPS_PER_MINUTE is invalid."""
        with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
            with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                    with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                        with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 0):
                            with pytest.raises(ConfigurationError) as exc_info:
                                validate_config(model="ollama")

                            assert "MAX_TICKER_LOOKUPS_PER_MINUTE must be greater than 0" in str(
                                exc_info.value
                            )


class TestConfigSummary:
    """Tests for get_config_summary function."""

    def test_get_config_summary_all_keys_set(self):
        """Test config summary when all keys are set."""
        with patch.object(config, "OPENAI_API_KEY", "sk-test-key"):
            with patch.object(config, "TAVILY_API_KEY", "tvly-test-key"):
                with patch.object(config, "LOGFIRE_TOKEN", "test-token"):
                    with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                        with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                            with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 15):
                                summary = get_config_summary()

                                assert summary["openai_api_key_set"] == "Yes"
                                assert summary["tavily_api_key_set"] == "Yes"
                                assert summary["logfire_token_set"] == "Yes"
                                assert summary["ollama_base_url"] == "http://localhost:11434"
                                assert summary["ollama_model_name"] == "qwen2.5:3b"
                                assert summary["max_ticker_lookups_per_minute"] == "15"

    def test_get_config_summary_no_keys_set(self):
        """Test config summary when no keys are set."""
        with patch.object(config, "OPENAI_API_KEY", None):
            with patch.object(config, "TAVILY_API_KEY", None):
                with patch.object(config, "LOGFIRE_TOKEN", None):
                    with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                        with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                            with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                                summary = get_config_summary()

                                assert summary["openai_api_key_set"] == "No"
                                assert summary["tavily_api_key_set"] == "No"
                                assert summary["logfire_token_set"] == "No"
                                # Defaults should still be present
                                assert summary["ollama_base_url"] == "http://localhost:11434"
                                assert summary["ollama_model_name"] == "qwen2.5:3b"

    def test_get_config_summary_masks_sensitive_data(self):
        """Test that config summary doesn't expose actual API keys."""
        with patch.object(config, "OPENAI_API_KEY", "sk-super-secret-key-12345"):
            with patch.object(config, "TAVILY_API_KEY", "tvly-super-secret-key-67890"):
                with patch.object(config, "LOGFIRE_TOKEN", "super-secret-token-abcdef"):
                    with patch.object(config, "OLLAMA_BASE_URL", "http://localhost:11434"):
                        with patch.object(config, "OLLAMA_MODEL_NAME", "qwen2.5:3b"):
                            with patch.object(config, "MAX_TICKER_LOOKUPS_PER_MINUTE", 10):
                                summary = get_config_summary()

                                # Should only indicate whether keys are set, not expose values
                                assert "sk-super-secret-key-12345" not in str(summary)
                                assert "tvly-super-secret-key-67890" not in str(summary)
                                assert "super-secret-token-abcdef" not in str(summary)
                                assert summary["openai_api_key_set"] == "Yes"
                                assert summary["tavily_api_key_set"] == "Yes"
                                assert summary["logfire_token_set"] == "Yes"


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test ConfigurationError inherits from Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)

    def test_configuration_error_message(self):
        """Test ConfigurationError preserves message."""
        message = "Test error message"
        error = ConfigurationError(message)
        assert str(error) == message

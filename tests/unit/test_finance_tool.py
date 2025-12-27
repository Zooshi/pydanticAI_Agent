"""Unit tests for finance_tool module.

This module tests the get_stock_price() function including:
- Successful stock price lookups
- Rate limiting enforcement
- Invalid ticker handling
- API error handling
- Network failure scenarios
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.utils.exceptions import RateLimitExceededError, ToolExecutionError
from src.tools.finance_tool import get_stock_price, get_rate_limiter


class TestGetStockPriceSuccess:
    """Test successful stock price lookups."""

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_valid_ticker_returns_complete_data(self, mock_ticker_class):
        """Test successful lookup with all fields present."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "currentPrice": 150.25,
            "previousClose": 149.80,
            "dayHigh": 151.00,
            "dayLow": 149.50,
            "volume": 50000000,
            "currency": "USD",
        }
        mock_ticker_class.return_value = mock_ticker

        # Act
        result = get_stock_price("AAPL")

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["current_price"] == 150.25
        assert result["previous_close"] == 149.80
        assert result["day_high"] == 151.00
        assert result["day_low"] == 149.50
        assert result["volume"] == 50000000
        assert result["currency"] == "USD"
        mock_ticker_class.assert_called_once_with("AAPL")

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_lowercase_ticker_converts_to_uppercase(self, mock_ticker_class):
        """Test that lowercase ticker is converted to uppercase."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "currentPrice": 100.0,
            "previousClose": 99.0,
            "currency": "USD",
        }
        mock_ticker_class.return_value = mock_ticker

        # Act
        result = get_stock_price("msft")

        # Assert
        assert result["ticker"] == "MSFT"
        mock_ticker_class.assert_called_once_with("MSFT")

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_ticker_with_whitespace_is_trimmed(self, mock_ticker_class):
        """Test that ticker with leading/trailing whitespace is trimmed."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "currentPrice": 200.0,
            "previousClose": 198.0,
            "currency": "USD",
        }
        mock_ticker_class.return_value = mock_ticker

        # Act
        result = get_stock_price("  GOOGL  ")

        # Assert
        assert result["ticker"] == "GOOGL"
        mock_ticker_class.assert_called_once_with("GOOGL")

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_uses_regularMarketPrice_fallback(self, mock_ticker_class):
        """Test fallback to regularMarketPrice when currentPrice is missing."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "regularMarketPrice": 145.50,
            "previousClose": 144.00,
            "regularMarketDayHigh": 146.00,
            "regularMarketDayLow": 143.50,
            "regularMarketVolume": 30000000,
            "currency": "USD",
        }
        mock_ticker_class.return_value = mock_ticker

        # Act
        result = get_stock_price("TSLA")

        # Assert
        assert result["current_price"] == 145.50
        assert result["day_high"] == 146.00
        assert result["day_low"] == 143.50
        assert result["volume"] == 30000000

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_uses_previousClose_as_last_fallback(self, mock_ticker_class):
        """Test fallback to previousClose when both current and regular prices missing."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "previousClose": 100.00,
            "currency": "EUR",
        }
        mock_ticker_class.return_value = mock_ticker

        # Act
        result = get_stock_price("SAP")

        # Assert
        assert result["current_price"] == 100.00
        assert result["currency"] == "EUR"

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_defaults_missing_fields_to_zero_or_default(self, mock_ticker_class):
        """Test that missing optional fields default to 0 or default values."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "currentPrice": 75.00,
            "symbol": "AMD",  # Need at least 2 fields to pass validation
            # Missing: previousClose, dayHigh, dayLow, volume, currency
        }
        mock_ticker_class.return_value = mock_ticker

        # Act
        result = get_stock_price("AMD")

        # Assert
        assert result["current_price"] == 75.00
        assert result["previous_close"] == 0.0
        assert result["day_high"] == 0.0
        assert result["day_low"] == 0.0
        assert result["volume"] == 0
        assert result["currency"] == "USD"  # Default currency


class TestGetStockPriceRateLimiting:
    """Test rate limiting behavior."""

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_rate_limit_exceeded_raises_error(self, mock_ticker_class):
        """Test that exceeding rate limit raises RateLimitExceededError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {"currentPrice": 100.0, "currency": "USD"}
        mock_ticker_class.return_value = mock_ticker

        # Act: Make 10 successful requests
        for _ in range(10):
            get_stock_price("AAPL")

        # Assert: 11th request should raise RateLimitExceededError
        with pytest.raises(RateLimitExceededError) as exc_info:
            get_stock_price("AAPL")

        assert "Rate limit exceeded" in str(exc_info.value)
        assert "10 requests" in str(exc_info.value)

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_rate_limit_includes_wait_time(self, mock_ticker_class):
        """Test that rate limit error includes wait time in message."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {"currentPrice": 100.0, "currency": "USD"}
        mock_ticker_class.return_value = mock_ticker

        # Act: Exhaust rate limit
        for _ in range(10):
            get_stock_price("AAPL")

        # Assert: Error message includes wait time
        with pytest.raises(RateLimitExceededError) as exc_info:
            get_stock_price("AAPL")

        error_message = str(exc_info.value)
        assert "wait" in error_message.lower()
        assert "seconds" in error_message.lower()


class TestGetStockPriceInvalidInput:
    """Test invalid input handling."""

    def test_get_stock_price_empty_string_raises_error(self):
        """Test that empty ticker string raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("")

        assert "Invalid ticker format" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_get_stock_price_whitespace_only_raises_error(self):
        """Test that whitespace-only ticker raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("   ")

        assert "Invalid ticker format" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_get_stock_price_none_raises_error(self):
        """Test that None ticker raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price(None)

        assert "Invalid ticker format" in str(exc_info.value)

    def test_get_stock_price_non_string_raises_error(self):
        """Test that non-string ticker raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price(12345)

        assert "Invalid ticker format" in str(exc_info.value)
        assert "int" in str(exc_info.value)

    def test_get_stock_price_too_long_ticker_raises_error(self):
        """Test that ticker longer than 10 characters raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("VERYLONGTICKER123")

        assert "Invalid ticker format" in str(exc_info.value)
        assert "maximum length" in str(exc_info.value).lower()


class TestGetStockPriceAPIErrors:
    """Test API error handling."""

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_invalid_ticker_not_found_raises_error(self, mock_ticker_class):
        """Test that invalid/not found ticker raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {}  # Empty response indicates not found
        mock_ticker_class.return_value = mock_ticker

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("INVALID")

        assert "not found" in str(exc_info.value).lower()
        assert "INVALID" in str(exc_info.value)

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_minimal_info_response_raises_error(self, mock_ticker_class):
        """Test that response with only one field raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {"symbol": "TEST"}  # Only one field, no price data
        mock_ticker_class.return_value = mock_ticker

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("TEST")

        assert "not found" in str(exc_info.value).lower() or "no data" in str(exc_info.value).lower()

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_no_price_data_raises_error(self, mock_ticker_class):
        """Test that response without any price field raises ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker = Mock()
        mock_ticker.info = {
            "symbol": "NOPRICE",
            "currency": "USD",
            "volume": 1000000,
            # Missing all price fields
        }
        mock_ticker_class.return_value = mock_ticker

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("NOPRICE")

        assert "No price data available" in str(exc_info.value)
        assert "NOPRICE" in str(exc_info.value)

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_yfinance_exception_wrapped_in_tool_error(self, mock_ticker_class):
        """Test that YFinance exceptions are wrapped in ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker_class.side_effect = ConnectionError("Network unreachable")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("AAPL")

        assert "YFinance API error" in str(exc_info.value)
        assert "AAPL" in str(exc_info.value)
        assert "ConnectionError" in str(exc_info.value)
        assert "Network unreachable" in str(exc_info.value)

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_timeout_error_wrapped(self, mock_ticker_class):
        """Test that timeout exceptions are wrapped in ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker_class.side_effect = TimeoutError("Request timed out")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("SLOW")

        assert "YFinance API error" in str(exc_info.value)
        assert "SLOW" in str(exc_info.value)
        assert "TimeoutError" in str(exc_info.value)

    @patch("src.tools.finance_tool.yf.Ticker")
    def test_get_stock_price_generic_exception_wrapped(self, mock_ticker_class):
        """Test that generic exceptions are wrapped in ToolExecutionError."""
        # Arrange
        get_rate_limiter().reset_time()
        mock_ticker_class.side_effect = RuntimeError("Unexpected error")

        # Act & Assert
        with pytest.raises(ToolExecutionError) as exc_info:
            get_stock_price("ERROR")

        assert "YFinance API error" in str(exc_info.value)
        assert "ERROR" in str(exc_info.value)
        assert "RuntimeError" in str(exc_info.value)


class TestGetRateLimiter:
    """Test rate limiter accessor function."""

    def test_get_rate_limiter_returns_limiter_instance(self):
        """Test that get_rate_limiter() returns the global RateLimiter."""
        # Act
        limiter = get_rate_limiter()

        # Assert
        from src.utils.rate_limiter import RateLimiter
        assert isinstance(limiter, RateLimiter)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

"""Finance tool for stock price lookup using YFinance.

This module provides a tool function for retrieving real-time stock price
information from Yahoo Finance. It integrates with the rate limiter to
enforce API usage quotas and provides structured financial data.

The tool is designed to be called by PydanticAI agents with ticker symbols
that have already been converted from company names (e.g., "Apple" -> "AAPL").
"""

from typing import Any

import yfinance as yf

from src.utils.exceptions import ToolExecutionError
from src.utils.rate_limiter import RateLimiter

# Global rate limiter instance: 10 ticker lookups per minute
_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def get_stock_price(ticker: str) -> dict[str, Any]:
    """Fetch current stock price and financial data for a given ticker.

    This function retrieves real-time stock market data from Yahoo Finance,
    including current price, previous close, daily high/low, volume, and
    currency. It enforces rate limiting (10 requests per minute) to prevent
    API abuse.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL').
            Must be a valid ticker recognized by Yahoo Finance.

    Returns:
        Dictionary containing structured financial data:
        {
            "ticker": str,           # The ticker symbol (uppercase)
            "current_price": float,  # Current/latest trading price
            "previous_close": float, # Previous day's closing price
            "day_high": float,       # Highest price today
            "day_low": float,        # Lowest price today
            "volume": int,           # Trading volume
            "currency": str          # Currency code (e.g., 'USD')
        }

    Raises:
        RateLimitExceededError: If the rate limit (10 requests/min) is
            exceeded. Error message includes wait time in seconds.
        ToolExecutionError: If the ticker is invalid, not found, or the
            YFinance API encounters an error. Error message includes
            ticker symbol and failure reason.

    Example:
        >>> data = get_stock_price("AAPL")
        >>> print(f"Current price: ${data['current_price']}")
        Current price: $150.25
    """
    # Validate ticker format
    if not ticker or not isinstance(ticker, str):
        raise ToolExecutionError(
            f"Invalid ticker format: ticker must be a non-empty string, got {type(ticker).__name__}"
        )

    ticker = ticker.strip().upper()

    if not ticker:
        raise ToolExecutionError("Invalid ticker format: ticker cannot be empty or whitespace")

    if len(ticker) > 10:
        raise ToolExecutionError(
            f"Invalid ticker format: ticker '{ticker}' exceeds maximum length of 10 characters"
        )

    # Check rate limit before making API call
    _rate_limiter.check_and_record()

    try:
        # Fetch ticker data from YFinance
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        # Validate that we received meaningful data
        if not info or len(info) <= 1:
            raise ToolExecutionError(
                f"Ticker '{ticker}' not found or no data available. "
                "Please verify the ticker symbol is correct."
            )

        # Extract required fields with fallbacks
        # YFinance can return different field names depending on the ticker type
        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )

        if current_price is None:
            raise ToolExecutionError(
                f"No price data available for ticker '{ticker}'. "
                "This may be an invalid ticker or the market is closed."
            )

        previous_close = info.get("previousClose")
        day_high = info.get("dayHigh") or info.get("regularMarketDayHigh")
        day_low = info.get("dayLow") or info.get("regularMarketDayLow")
        volume = info.get("volume") or info.get("regularMarketVolume")
        currency = info.get("currency", "USD")

        # Build response dictionary
        return {
            "ticker": ticker,
            "current_price": float(current_price) if current_price is not None else 0.0,
            "previous_close": float(previous_close) if previous_close is not None else 0.0,
            "day_high": float(day_high) if day_high is not None else 0.0,
            "day_low": float(day_low) if day_low is not None else 0.0,
            "volume": int(volume) if volume is not None else 0,
            "currency": str(currency),
        }

    except ToolExecutionError:
        # Re-raise our custom errors without wrapping
        raise

    except Exception as e:
        # Wrap unexpected errors with context
        raise ToolExecutionError(
            f"YFinance API error for ticker '{ticker}': {type(e).__name__}: {str(e)}"
        )


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance for testing purposes.

    Returns:
        The global RateLimiter instance used by get_stock_price()
    """
    return _rate_limiter

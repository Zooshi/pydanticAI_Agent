"""Rate limiter utility using sliding window algorithm.

This module provides a thread-safe rate limiter implementation to prevent
API abuse and enforce request quotas.
"""

import threading
import time
from collections import deque
from typing import Deque


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded.

    This exception is raised when a request would exceed the configured
    rate limit. The error message includes the wait time in seconds before
    the next request can be made.
    """
    pass


class RateLimiter:
    """Thread-safe sliding window rate limiter.

    Tracks request timestamps in a sliding window and enforces a maximum
    number of requests per time period. Uses a deque for efficient timestamp
    management and threading.Lock for thread safety.

    Attributes:
        max_requests: Maximum number of requests allowed in the time window
        window_seconds: Time window duration in seconds
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        """Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in time window.
                Defaults to 10.
            window_seconds: Time window duration in seconds. Defaults to 60.

        Raises:
            ValueError: If max_requests or window_seconds is less than 1
        """
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: Deque[float] = deque()
        self._lock = threading.Lock()

    def _remove_expired_timestamps(self, current_time: float) -> None:
        """Remove timestamps that are outside the sliding window.

        Args:
            current_time: Current timestamp in seconds since epoch
        """
        cutoff_time = current_time - self.window_seconds
        while self._timestamps and self._timestamps[0] <= cutoff_time:
            self._timestamps.popleft()

    def check_and_record(self) -> None:
        """Check rate limit and record current request timestamp.

        This method removes expired timestamps, checks if the request would
        exceed the rate limit, and records the current timestamp if allowed.

        Raises:
            RateLimitExceededError: If adding this request would exceed the
                rate limit. Error message includes wait time in seconds.
        """
        with self._lock:
            current_time = time.time()
            self._remove_expired_timestamps(current_time)

            if len(self._timestamps) >= self.max_requests:
                # Calculate wait time until oldest timestamp expires
                oldest_timestamp = self._timestamps[0]
                wait_time = oldest_timestamp + self.window_seconds - current_time
                wait_time = max(0.0, wait_time)  # Ensure non-negative

                raise RateLimitExceededError(
                    f"Rate limit exceeded. Maximum {self.max_requests} requests "
                    f"per {self.window_seconds} seconds. Please wait "
                    f"{wait_time:.1f} seconds before retrying."
                )

            self._timestamps.append(current_time)

    def get_remaining_requests(self) -> int:
        """Get the number of requests remaining in the current window.

        Returns:
            Number of requests that can be made without exceeding the limit.
            Returns 0 if the limit is reached.
        """
        with self._lock:
            current_time = time.time()
            self._remove_expired_timestamps(current_time)
            return max(0, self.max_requests - len(self._timestamps))

    def reset_time(self) -> None:
        """Reset the rate limiter by clearing all recorded timestamps.

        This method is primarily intended for testing purposes to reset
        the limiter state between test cases.
        """
        with self._lock:
            self._timestamps.clear()

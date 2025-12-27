"""Unit tests for rate limiter utility."""

import threading
import time
from unittest.mock import patch

import pytest

from src.utils.rate_limiter import RateLimiter, RateLimitExceededError


class TestRateLimiterInitialization:
    """Test cases for RateLimiter initialization."""

    def test_initialization_with_defaults(self) -> None:
        """Test rate limiter initialization with default parameters."""
        limiter = RateLimiter()
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60

    def test_initialization_with_custom_values(self) -> None:
        """Test rate limiter initialization with custom parameters."""
        limiter = RateLimiter(max_requests=5, window_seconds=30)
        assert limiter.max_requests == 5
        assert limiter.window_seconds == 30

    def test_initialization_invalid_max_requests(self) -> None:
        """Test initialization fails with invalid max_requests."""
        with pytest.raises(ValueError, match="max_requests must be at least 1"):
            RateLimiter(max_requests=0)

    def test_initialization_invalid_window_seconds(self) -> None:
        """Test initialization fails with invalid window_seconds."""
        with pytest.raises(ValueError, match="window_seconds must be at least 1"):
            RateLimiter(max_requests=10, window_seconds=0)


class TestRateLimiterBasicFunctionality:
    """Test cases for basic rate limiting functionality."""

    def test_allows_requests_under_limit(self) -> None:
        """Test that requests under the limit are allowed."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Should allow first 3 requests without raising
        limiter.check_and_record()
        limiter.check_and_record()
        limiter.check_and_record()

    def test_blocks_requests_exceeding_limit(self) -> None:
        """Test that requests exceeding the limit are blocked."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # First 2 requests should succeed
        limiter.check_and_record()
        limiter.check_and_record()

        # Third request should raise RateLimitExceededError
        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.check_and_record()

        # Verify error message contains relevant information
        error_message = str(exc_info.value)
        assert "Rate limit exceeded" in error_message
        assert "2 requests" in error_message
        assert "60 seconds" in error_message
        assert "wait" in error_message.lower()

    def test_get_remaining_requests_initial(self) -> None:
        """Test get_remaining_requests returns correct count initially."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.get_remaining_requests() == 5

    def test_get_remaining_requests_after_usage(self) -> None:
        """Test get_remaining_requests decreases after requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        limiter.check_and_record()
        assert limiter.get_remaining_requests() == 4

        limiter.check_and_record()
        limiter.check_and_record()
        assert limiter.get_remaining_requests() == 2

    def test_get_remaining_requests_at_limit(self) -> None:
        """Test get_remaining_requests returns 0 at limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        limiter.check_and_record()
        limiter.check_and_record()

        assert limiter.get_remaining_requests() == 0


class TestRateLimiterSlidingWindow:
    """Test cases for sliding window behavior."""

    def test_window_expiration_allows_new_requests(self) -> None:
        """Test that expired timestamps are removed from window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)

        # Make 2 requests to reach limit
        limiter.check_and_record()
        limiter.check_and_record()

        # Should be at limit
        with pytest.raises(RateLimitExceededError):
            limiter.check_and_record()

        # Wait for window to expire
        time.sleep(1.1)

        # Should now allow a new request
        limiter.check_and_record()

    def test_partial_window_expiration(self) -> None:
        """Test that only expired timestamps are removed."""
        limiter = RateLimiter(max_requests=3, window_seconds=2)

        # Make first request
        limiter.check_and_record()

        # Wait 1 second
        time.sleep(1)

        # Make two more requests
        limiter.check_and_record()
        limiter.check_and_record()

        # Should be at limit
        with pytest.raises(RateLimitExceededError):
            limiter.check_and_record()

        # Wait for first timestamp to expire (total 2+ seconds from start)
        time.sleep(1.1)

        # Should now allow one new request (first expired, 2 remain)
        limiter.check_and_record()

    @patch("time.time")
    def test_sliding_window_calculation(self, mock_time) -> None:
        """Test sliding window behavior with mocked time."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Set initial time to 0
        mock_time.return_value = 0.0

        # Make 2 requests at time=0
        limiter.check_and_record()
        limiter.check_and_record()

        # Third request should fail
        with pytest.raises(RateLimitExceededError):
            limiter.check_and_record()

        # Move time forward by 61 seconds (past window)
        mock_time.return_value = 61.0

        # Should now allow new requests (old timestamps expired)
        limiter.check_and_record()
        assert limiter.get_remaining_requests() == 1


class TestRateLimiterThreadSafety:
    """Test cases for thread safety."""

    def test_concurrent_requests_thread_safe(self) -> None:
        """Test that concurrent requests are handled safely."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        successful_requests = []
        failed_requests = []

        def make_request(request_id: int) -> None:
            try:
                limiter.check_and_record()
                successful_requests.append(request_id)
            except RateLimitExceededError:
                failed_requests.append(request_id)

        # Create 15 threads to exceed limit of 10
        threads = []
        for i in range(15):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have exactly 10 successful requests
        assert len(successful_requests) == 10
        # And 5 failed requests
        assert len(failed_requests) == 5
        # Total should be 15
        assert len(successful_requests) + len(failed_requests) == 15

    def test_get_remaining_requests_thread_safe(self) -> None:
        """Test get_remaining_requests is thread-safe."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        results = []

        def check_remaining() -> None:
            remaining = limiter.get_remaining_requests()
            results.append(remaining)

        # Make 3 requests
        limiter.check_and_record()
        limiter.check_and_record()
        limiter.check_and_record()

        # Check remaining from multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=check_remaining)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should see the same remaining count
        assert all(r == 2 for r in results)


class TestRateLimiterResetAndEdgeCases:
    """Test cases for reset functionality and edge cases."""

    def test_reset_time_clears_timestamps(self) -> None:
        """Test reset_time clears all recorded timestamps."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Make 2 requests to reach limit
        limiter.check_and_record()
        limiter.check_and_record()

        # Should be at limit
        with pytest.raises(RateLimitExceededError):
            limiter.check_and_record()

        # Reset the limiter
        limiter.reset_time()

        # Should now allow new requests
        limiter.check_and_record()
        assert limiter.get_remaining_requests() == 1

    def test_single_request_limit(self) -> None:
        """Test rate limiter with max_requests=1."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # First request should succeed
        limiter.check_and_record()

        # Second request should fail immediately
        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.check_and_record()

        # Error should indicate single request limit
        assert "1 requests" in str(exc_info.value)

    def test_wait_time_calculation_accuracy(self) -> None:
        """Test that wait time in error message is accurate."""
        limiter = RateLimiter(max_requests=1, window_seconds=10)

        # Make first request
        limiter.check_and_record()

        # Wait 3 seconds
        time.sleep(3)

        # Try second request (should fail with 7 second wait time)
        with pytest.raises(RateLimitExceededError) as exc_info:
            limiter.check_and_record()

        error_message = str(exc_info.value)

        # Extract wait time from error message
        # Format: "... wait X.X seconds ..."
        # Wait time should be approximately 7 seconds (10 - 3)
        # Allow some tolerance for execution time
        assert "6." in error_message or "7." in error_message

    def test_multiple_reset_cycles(self) -> None:
        """Test multiple reset and usage cycles."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        for _ in range(3):
            # Use up the limit
            limiter.check_and_record()
            limiter.check_and_record()

            # Verify at limit
            assert limiter.get_remaining_requests() == 0

            # Reset
            limiter.reset_time()

            # Verify reset worked
            assert limiter.get_remaining_requests() == 2

    @patch("time.time")
    def test_zero_wait_time_at_boundary(self, mock_time) -> None:
        """Test that wait time is 0 when exactly at window boundary."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Make request at time=0
        mock_time.return_value = 0.0
        limiter.check_and_record()

        # Try to make another request at exactly time=60 (window boundary)
        mock_time.return_value = 60.0

        # Should succeed because old timestamp expired
        limiter.check_and_record()
        assert limiter.get_remaining_requests() == 0

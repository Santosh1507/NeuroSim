"""Tests for rate_limiter module."""
import pytest
from rate_limiter import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is False

    def test_different_ips_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("1.1.1.1") is True
        assert limiter.is_allowed("1.1.1.1") is False
        assert limiter.is_allowed("2.2.2.2") is True

    def test_remaining_count(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.remaining("127.0.0.1") == 5
        limiter.is_allowed("127.0.0.1")
        limiter.is_allowed("127.0.0.1")
        assert limiter.remaining("127.0.0.1") == 3

    def test_window_expiry(self):
        import time
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is False
        
        original_time = time.time
        try:
            time.time = lambda: original_time() + 2
            assert limiter.is_allowed("127.0.0.1") is True
        finally:
            time.time = original_time

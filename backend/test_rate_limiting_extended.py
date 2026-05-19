"""Extended rate limiter tests."""
import pytest
import time
from rate_limiter import RateLimiter


class TestRateLimiterExtended:
    def test_reset_clears_requests(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("1.2.3.4")
        limiter.reset("1.2.3.4")
        assert limiter.is_allowed("1.2.3.4")

    def test_different_ips_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("1.1.1.1")
        assert not limiter.is_allowed("1.1.1.1")
        assert limiter.is_allowed("2.2.2.2")

    def test_remaining_count(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.is_allowed("1.2.3.4")
        limiter.is_allowed("1.2.3.4")
        assert limiter.remaining("1.2.3.4") == 3

    def test_window_expiry_allows_again(self, monkeypatch):
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.is_allowed("1.2.3.4")
        assert not limiter.is_allowed("1.2.3.4")
        original_time = time.time()
        monkeypatch.setattr(time, "time", lambda: original_time + 2)
        assert limiter.is_allowed("1.2.3.4")

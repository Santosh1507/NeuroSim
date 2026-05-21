"""Tests for rate_limiter module."""

from unittest.mock import MagicMock

from rate_limiter import RateLimiter, get_client_ip


def _mock_request(headers: dict | None = None, client_host: str = "8.8.8.8"):
    """Build a minimal FastAPI-style Request mock for get_client_ip tests."""
    req = MagicMock()
    req.headers = headers or {}
    req.client.host = client_host
    return req


class TestGetClientIp:
    def test_x_forwarded_for_single_ip(self):
        req = _mock_request({"X-Forwarded-For": "203.0.113.42"})
        assert get_client_ip(req) == "203.0.113.42"

    def test_x_forwarded_for_multi_hop(self):
        """Leftmost IP is the original client."""
        req = _mock_request({"X-Forwarded-For": "203.0.113.42, 10.0.0.1, 10.0.0.2"})
        assert get_client_ip(req) == "203.0.113.42"

    def test_x_forwarded_for_precedence(self):
        """X-Forwarded-For beats X-Real-IP and client.host."""
        req = _mock_request(
            {"X-Forwarded-For": "1.1.1.1", "X-Real-IP": "2.2.2.2"},
            client_host="3.3.3.3",
        )
        assert get_client_ip(req) == "1.1.1.1"

    def test_x_real_ip_fallback(self):
        """When X-Forwarded-For is absent, falls back to X-Real-IP."""
        req = _mock_request({"X-Real-IP": "4.4.4.4"}, client_host="5.5.5.5")
        assert get_client_ip(req) == "4.4.4.4"

    def test_client_host_fallback(self):
        """When no proxy headers, falls back to request.client.host."""
        req = _mock_request(client_host="6.6.6.6")
        assert get_client_ip(req) == "6.6.6.6"

    def test_unknown_when_no_client(self):
        """When neither headers nor client are available, returns 'unknown'."""
        req = MagicMock()
        req.headers = {}
        req.client = None
        assert get_client_ip(req) == "unknown"

    def test_handles_empty_x_forwarded_for(self):
        """Empty X-Forwarded-For falls through to next resolution step."""
        req = _mock_request({"X-Forwarded-For": ""}, client_host="7.7.7.7")
        assert get_client_ip(req) == "7.7.7.7"

    def test_handles_whitespace_x_forwarded_for(self):
        """Whitespace-only X-Forwarded-For falls through."""
        req = _mock_request({"X-Forwarded-For": "   "}, client_host="8.8.8.8")
        assert get_client_ip(req) == "8.8.8.8"


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

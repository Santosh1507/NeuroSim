"""Simple in-memory rate limiting middleware for FastAPI.

IP-based, sliding window. Lightweight — no Redis, no external deps.
Configurable per-endpoint via the rate_limiter decorator.

When deployed behind a reverse proxy (Render, nginx, etc.),
client IP is resolved from X-Forwarded-For or X-Real-IP headers
rather than request.client.host (which sees the proxy IP).
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from config import settings
from fastapi import HTTPException, Request


def get_client_ip(request: Request) -> str:
    """Extract the real client IP from a request, respecting reverse proxy headers.

    Resolution order:
      1. X-Forwarded-For header (first IP — the original client)
      2. X-Real-IP header
      3. request.client.host (direct connection / no proxy)

    Render, nginx, and most cloud proxies set X-Forwarded-For with the
    actual client IP.  The leftmost value is the original client; any
    subsequent values are intermediate proxies added by each hop.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
        if ip:
            return ip
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Sliding window rate limiter keyed by IP address."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, ip: str):
        cutoff = time.time() - self.window_seconds
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def is_allowed(self, ip: str) -> bool:
        self._cleanup(ip)
        if len(self._requests[ip]) >= self.max_requests:
            return False
        self._requests[ip].append(time.time())
        return True

    def remaining(self, ip: str) -> int:
        self._cleanup(ip)
        return max(0, self.max_requests - len(self._requests[ip]))

    def reset(self, ip: str) -> None:
        self._requests[ip] = []


def rate_limit(limiter: RateLimiter):
    """Decorator that applies rate limiting to a FastAPI route."""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if request:
                client_ip = get_client_ip(request)
                if not limiter.is_allowed(client_ip):
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Try again in {limiter.window_seconds}s.",
                    )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Default limiters — values from config.py (env-configurable)
upload_limiter = RateLimiter(max_requests=settings.rate_limit_upload_requests, window_seconds=settings.rate_limit_upload_window)
api_limiter = RateLimiter(max_requests=settings.rate_limit_api_requests, window_seconds=settings.rate_limit_api_window)
predict_limiter = RateLimiter(max_requests=settings.rate_limit_predict_requests, window_seconds=settings.rate_limit_predict_window)
auth_limiter = RateLimiter(max_requests=settings.rate_limit_auth_requests, window_seconds=settings.rate_limit_auth_window)


def check_api_limit(request: Request):
    ip = get_client_ip(request)
    if not api_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Too many requests, please slow down.",
        )


def check_predict_limit(request: Request):
    """Stricter rate limit for /predict to protect Gemini API quota."""
    ip = get_client_ip(request)
    if not predict_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=429,
            detail="Predict rate limit exceeded. Max 10 predictions per minute. Please slow down.",
        )

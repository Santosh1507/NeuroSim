"""Simple in-memory rate limiting middleware for FastAPI.

IP-based, sliding window. Lightweight — no Redis, no external deps.
Configurable per-endpoint via the rate_limiter decorator.
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request


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
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            if not limiter.is_allowed(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {limiter.window_seconds}s.",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# Default limiters
upload_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 uploads per 5 min
api_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 API calls per min


def check_api_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not api_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Too many requests, please slow down.",
        )

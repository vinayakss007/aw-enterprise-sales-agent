"""Sliding-window rate limiting middleware.

In-memory backend by default (one bucket per process). Multi-instance
deployments should swap in a Redis backend; the ``RateLimiter`` interface
keeps that change isolated to a single class.

Rate limits are keyed by:
  * ``Authorization`` header when present (so authenticated callers are
    bucketed independently from anonymous traffic), else
  * client IP address.

Probes ``/api/v1/health/*`` and ``/metrics`` are exempt — these need to be
callable at any frequency by load balancers and Prometheus.
"""
from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from threading import Lock
from typing import Protocol

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


def _bucket_key(request: Request) -> str:
    """Identify the caller for rate-limiting purposes."""
    auth = request.headers.get("authorization")
    if auth:
        # Hash the bearer so we don't keep raw tokens in process memory.
        return "auth:" + hashlib.sha256(auth.encode("utf-8")).hexdigest()[:16]
    if request.client:
        return f"ip:{request.client.host}"
    return "anonymous"


class RateLimiter(Protocol):
    def hit(self, key: str, *, limit: int, window: float, now: float) -> tuple[bool, int]:
        """Return ``(allowed, retry_after_seconds)`` for a single hit."""


class InMemoryRateLimiter:
    """Sliding-window counter backed by a deque per key."""

    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, key: str, *, limit: int, window: float, now: float) -> tuple[bool, int]:
        cutoff = now - window
        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(bucket[0] + window - now))
                return False, retry_after
            bucket.append(now)
            return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply ``limit`` requests per ``window`` seconds per caller."""

    def __init__(
        self,
        app,
        *,
        limit: int = 100,
        window: float = 60.0,
        exempt_paths: Iterable[str] = ("/api/v1/health", "/metrics"),
        limiter: RateLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.exempt_prefixes = tuple(exempt_paths)
        self.limiter: RateLimiter = limiter or InMemoryRateLimiter()

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self.exempt_prefixes)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        if self._is_exempt(request.url.path):
            return await call_next(request)

        key = _bucket_key(request)
        allowed, retry_after = self.limiter.hit(
            key, limit=self.limit, window=self.window, now=time.monotonic()
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)


__all__ = [
    "RateLimitMiddleware",
    "InMemoryRateLimiter",
    "RateLimiter",
]

"""Sliding-window rate limiting middleware.

Two backends ship in this module:

* ``InMemoryRateLimiter`` — one bucket per process, keyed in a ``defaultdict``
  protected by a thread lock. Good for single-instance dev and tests.
* ``RedisRateLimiter`` — sliding window backed by a Redis sorted set per
  caller. Multi-instance safe. Falls back to the in-memory limiter if the
  ``redis`` package isn't installed or the connection fails.

Rate limits are keyed by:
  * ``Authorization`` header when present (so authenticated callers are
    bucketed independently from anonymous traffic), else
  * client IP address.

Probes ``/api/v1/health/*`` and ``/metrics`` are exempt — these need to be
callable at any frequency by load balancers and Prometheus.
"""
from __future__ import annotations

import hashlib
import logging
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from threading import Lock
from typing import Protocol

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


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


class RedisRateLimiter:
    """Sliding-window limiter backed by a Redis sorted set per key.

    The set holds one member per recent request, scored by the request's
    monotonic timestamp. On each hit:

    1. Drop members older than ``now - window`` (``ZREMRANGEBYSCORE``).
    2. Count the surviving members (``ZCARD``).
    3. If under the limit, add the new request and bump the key's TTL.
    4. Otherwise, peek at the oldest member to compute ``retry_after``.

    If Redis errors out we *fail open* (allow the request) and log — being
    unable to reach Redis is an availability problem, not a security one.
    """

    def __init__(self, client: object, key_prefix: str = "rl:") -> None:
        # ``client`` is a ``redis.Redis`` instance. We type it as ``object``
        # so this module imports without redis installed; the build_default
        # factory chooses Redis vs InMemory at runtime.
        self._client = client
        self._prefix = key_prefix

    def hit(self, key: str, *, limit: int, window: float, now: float) -> tuple[bool, int]:
        full_key = f"{self._prefix}{key}"
        cutoff = now - window
        try:
            pipe = self._client.pipeline()  # type: ignore[attr-defined]
            pipe.zremrangebyscore(full_key, 0, cutoff)
            pipe.zcard(full_key)
            current_count = pipe.execute()[1]
            if current_count >= limit:
                oldest = self._client.zrange(  # type: ignore[attr-defined]
                    full_key, 0, 0, withscores=True
                )
                if oldest:
                    oldest_ts = float(oldest[0][1])
                    retry_after = max(1, int(oldest_ts + window - now))
                else:
                    retry_after = max(1, int(window))
                return False, retry_after
            # Member must be unique; suffix the count to deduplicate
            # near-simultaneous calls.
            member = f"{now:.6f}:{current_count}"
            pipe = self._client.pipeline()  # type: ignore[attr-defined]
            pipe.zadd(full_key, {member: now})
            pipe.expire(full_key, int(window) + 1)
            pipe.execute()
            return True, 0
        except Exception as exc:  # pragma: no cover — network defensive
            logger.warning("RedisRateLimiter.hit failed: %s — failing open", exc)
            return True, 0


def build_default_limiter(redis_url: str | None) -> RateLimiter:
    """Pick a backend at app startup.

    Returns a Redis-backed limiter when ``redis_url`` is set and the package
    is importable + ``ping`` succeeds; otherwise falls back to the in-memory
    limiter so dev / single-instance deployments keep working.
    """
    if not redis_url:
        return InMemoryRateLimiter()
    try:
        import redis  # type: ignore[import-not-found]

        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        logger.info("RateLimit: using Redis backend at %s", redis_url)
        return RedisRateLimiter(client)
    except Exception as exc:  # pragma: no cover — depends on env
        logger.warning(
            "RateLimit: Redis unavailable (%s) — falling back to in-memory", exc
        )
        return InMemoryRateLimiter()


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
    "RedisRateLimiter",
    "RateLimiter",
    "build_default_limiter",
]

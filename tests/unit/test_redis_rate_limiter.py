"""RedisRateLimiter unit tests using a fake Redis client.

The fake doesn't try to be a faithful Redis — just enough surface (zadd,
zremrangebyscore, zcard, zrange, expire, pipeline) to exercise the
``hit`` logic deterministically.
"""
from __future__ import annotations

from typing import Any


class _FakePipeline:
    def __init__(self, client: _FakeRedis) -> None:
        self.client = client
        self.commands: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str):
        # Record the call for later replay against the client.
        def recorder(*args: Any, **kwargs: Any):
            self.commands.append((name, args, kwargs))
            return self

        return recorder

    def execute(self) -> list[Any]:
        results: list[Any] = []
        for name, args, kwargs in self.commands:
            method = getattr(self.client, name)
            results.append(method(*args, **kwargs))
        self.commands.clear()
        return results


class _FakeRedis:
    def __init__(self) -> None:
        # key -> dict[member, score]
        self._zsets: dict[str, dict[str, float]] = {}

    def pipeline(self) -> _FakePipeline:
        return _FakePipeline(self)

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        zset = self._zsets.get(key, {})
        to_drop = [m for m, s in zset.items() if min_score <= s <= max_score]
        for member in to_drop:
            del zset[member]
        return len(to_drop)

    def zcard(self, key: str) -> int:
        return len(self._zsets.get(key, {}))

    def zadd(self, key: str, mapping: dict[str, float]) -> int:
        zset = self._zsets.setdefault(key, {})
        added = 0
        for member, score in mapping.items():
            if member not in zset:
                added += 1
            zset[member] = score
        return added

    def zrange(self, key: str, start: int, end: int, *, withscores: bool = False):
        zset = self._zsets.get(key, {})
        ordered = sorted(zset.items(), key=lambda kv: kv[1])
        # Redis end is inclusive; -1 means "last element".
        sliced = ordered[start : (end + 1) if end >= 0 else None]
        if withscores:
            return sliced
        return [m for m, _ in sliced]

    def expire(self, key: str, seconds: int) -> int:
        return 1

    def ping(self) -> bool:
        return True


def test_redis_limiter_allows_up_to_limit():
    from app.observability.rate_limit import RedisRateLimiter

    client = _FakeRedis()
    limiter = RedisRateLimiter(client)
    now = 1_000_000.0
    for i in range(5):
        allowed, retry = limiter.hit("alice", limit=5, window=60, now=now + i * 0.1)
        assert allowed, f"hit {i} should be allowed"
        assert retry == 0


def test_redis_limiter_blocks_over_limit_and_returns_retry_after():
    from app.observability.rate_limit import RedisRateLimiter

    client = _FakeRedis()
    limiter = RedisRateLimiter(client)
    now = 1_000_000.0
    for i in range(3):
        limiter.hit("alice", limit=3, window=60, now=now + i)
    blocked, retry = limiter.hit("alice", limit=3, window=60, now=now + 5)
    assert blocked is False
    assert retry >= 1


def test_redis_limiter_recovers_after_window_slides():
    from app.observability.rate_limit import RedisRateLimiter

    client = _FakeRedis()
    limiter = RedisRateLimiter(client)
    base = 1_000_000.0
    for i in range(3):
        limiter.hit("alice", limit=3, window=10, now=base + i * 0.1)
    blocked, _ = limiter.hit("alice", limit=3, window=10, now=base + 1)
    assert blocked is False
    # Past the window, all early hits expire.
    allowed, _ = limiter.hit("alice", limit=3, window=10, now=base + 100)
    assert allowed is True


def test_redis_limiter_independent_keys():
    from app.observability.rate_limit import RedisRateLimiter

    client = _FakeRedis()
    limiter = RedisRateLimiter(client)
    base = 1_000_000.0
    for i in range(3):
        limiter.hit("alice", limit=3, window=60, now=base + i)
    bob_allowed, _ = limiter.hit("bob", limit=3, window=60, now=base)
    assert bob_allowed is True


def test_redis_limiter_fails_open_on_redis_error():
    """If Redis raises, we allow the request (availability > strict limits)."""
    from app.observability.rate_limit import RedisRateLimiter

    class _Boom:
        def pipeline(self):
            raise RuntimeError("redis down")

    limiter = RedisRateLimiter(_Boom())
    allowed, retry = limiter.hit("alice", limit=1, window=60, now=0.0)
    assert allowed is True
    assert retry == 0


def test_build_default_limiter_returns_in_memory_when_no_url():
    from app.observability.rate_limit import (
        InMemoryRateLimiter,
        build_default_limiter,
    )

    assert isinstance(build_default_limiter(None), InMemoryRateLimiter)
    assert isinstance(build_default_limiter(""), InMemoryRateLimiter)

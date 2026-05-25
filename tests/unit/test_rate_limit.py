"""Rate limit middleware unit tests."""
from __future__ import annotations


def test_in_memory_limiter_allows_up_to_limit():
    from app.observability.rate_limit import InMemoryRateLimiter

    limiter = InMemoryRateLimiter()
    now = 1000.0
    for i in range(5):
        allowed, retry = limiter.hit("k", limit=5, window=60, now=now + i * 0.1)
        assert allowed, f"call {i} should be allowed"
        assert retry == 0


def test_in_memory_limiter_blocks_over_limit():
    from app.observability.rate_limit import InMemoryRateLimiter

    limiter = InMemoryRateLimiter()
    now = 1000.0
    for i in range(3):
        limiter.hit("k", limit=3, window=60, now=now + i * 0.1)
    allowed, retry = limiter.hit("k", limit=3, window=60, now=now + 0.5)
    assert allowed is False
    assert retry >= 1


def test_in_memory_limiter_recovers_after_window():
    from app.observability.rate_limit import InMemoryRateLimiter

    limiter = InMemoryRateLimiter()
    for i in range(3):
        limiter.hit("k", limit=3, window=10, now=100 + i * 0.1)
    blocked, _ = limiter.hit("k", limit=3, window=10, now=101)
    assert blocked is False
    # After window slides past the early hits, calls succeed again.
    allowed, _ = limiter.hit("k", limit=3, window=10, now=200)
    assert allowed is True


def test_in_memory_limiter_independent_keys():
    from app.observability.rate_limit import InMemoryRateLimiter

    limiter = InMemoryRateLimiter()
    for i in range(3):
        limiter.hit("alice", limit=3, window=60, now=100 + i)
    bob_allowed, _ = limiter.hit("bob", limit=3, window=60, now=100)
    assert bob_allowed is True


def test_middleware_returns_429_when_limit_exceeded():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.observability.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=2, window=60.0)

    @app.get("/echo")
    def echo():
        return {"ok": True}

    with TestClient(app) as client:
        assert client.get("/echo").status_code == 200
        assert client.get("/echo").status_code == 200
        blocked = client.get("/echo")
        assert blocked.status_code == 429
        body = blocked.json()
        assert body["detail"] == "Too many requests"
        assert body["retry_after_seconds"] >= 1
        assert "Retry-After" in blocked.headers


def test_middleware_exempts_health_path():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.observability.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=1, window=60.0)

    @app.get("/api/v1/health")
    def health():
        return {"ok": True}

    with TestClient(app) as client:
        for _ in range(10):
            assert client.get("/api/v1/health").status_code == 200


def test_middleware_keys_authed_users_separately_from_anon():
    """Two different bearer tokens get independent buckets."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.observability.rate_limit import RateLimitMiddleware

    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=1, window=60.0)

    @app.get("/r")
    def r():
        return {"ok": True}

    with TestClient(app) as client:
        a = {"Authorization": "Bearer aaa"}
        b = {"Authorization": "Bearer bbb"}
        assert client.get("/r", headers=a).status_code == 200
        # Same bearer is now over the limit.
        assert client.get("/r", headers=a).status_code == 429
        # Different bearer still has a fresh bucket.
        assert client.get("/r", headers=b).status_code == 200

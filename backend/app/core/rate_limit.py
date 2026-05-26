"""Rate limiting using slowapi with Redis backend (falls back to in-memory)."""
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_identifier(request: Request) -> str:
    """
    Rate limit key: prefer tenant_id from JWT, fall back to IP.
    This ensures per-tenant rate limiting for authenticated requests.
    """
    # Try to get tenant from header (set by auth middleware)
    tenant_id = request.headers.get("X-Tenant-Id")
    if tenant_id and tenant_id != "unknown":
        return f"tenant:{tenant_id}"
    return get_remote_address(request)


# Try Redis storage, fall back to in-memory
_storage_uri = None
try:
    import redis
    r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
    r.ping()
    _storage_uri = settings.REDIS_URL
    logger.info("Rate limiter using Redis storage")
except Exception:
    logger.info("Rate limiter using in-memory storage (Redis unavailable)")

limiter = Limiter(
    key_func=_get_identifier,
    storage_uri=_storage_uri,
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/minute"],
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": str(exc.detail),
        },
    )

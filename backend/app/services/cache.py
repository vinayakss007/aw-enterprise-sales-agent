"""Redis caching service with graceful degradation."""
import json
import logging
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client = None


def _get_redis():
    """Lazy-initialize Redis connection."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            _redis_client = None
    return _redis_client


class CacheService:
    """
    Redis-backed cache with automatic fallback to no-op when Redis is unavailable.
    App functions normally without Redis — just slower.
    """

    def __init__(self, prefix: str = "esa"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value. Returns None if not found or Redis unavailable."""
        client = _get_redis()
        if not client:
            return None
        try:
            value = client.get(self._key(key))
            return json.loads(value) if value else None
        except Exception as e:
            logger.debug(f"Cache get failed for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set a cached value with TTL. Returns False if Redis unavailable."""
        client = _get_redis()
        if not client:
            return False
        try:
            client.setex(self._key(key), ttl_seconds, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.debug(f"Cache set failed for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a cached key."""
        client = _get_redis()
        if not client:
            return False
        try:
            client.delete(self._key(key))
            return True
        except Exception as e:
            logger.debug(f"Cache delete failed for {key}: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        client = _get_redis()
        if not client:
            return 0
        try:
            keys = client.keys(self._key(pattern))
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache invalidate failed for {pattern}: {e}")
            return 0


# Singleton instances for common use cases
tenant_cache = CacheService(prefix="esa:tenant")
lead_cache = CacheService(prefix="esa:lead")
session_cache = CacheService(prefix="esa:session")

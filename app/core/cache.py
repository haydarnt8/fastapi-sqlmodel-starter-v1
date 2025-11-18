"""
Redis Cache Service

Provides Redis-based caching for:
- Token revocation (blacklisting JWTs on logout)
- Session management
- Rate limiting (future enhancement)
- General purpose caching

Why Redis for token revocation?
- JWT tokens are stateless (can't be invalidated server-side normally)
- With Redis, we can blacklist tokens when users logout
- Redis handles automatic expiration (TTL) perfectly for this use case
- Much faster than database queries

Features:
- Graceful degradation (app works without Redis, just logs warnings)
- Connection pooling for performance
- Automatic reconnection on failures
- Type-safe operations
"""

from typing import Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Async Redis cache service.

    Usage:
        from app.core.cache import get_redis_cache

        cache = await get_redis_cache()
        await cache.set("key", "value", ttl=3600)
        value = await cache.get("key")
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = settings.REDIS_ENABLED

    async def connect(self):
        """
        Connect to Redis server.

        Establishes connection pool for async operations.
        Falls back gracefully if Redis is unavailable.
        """
        if not self.enabled:
            logger.info("Redis is disabled in settings")
            return

        try:
            # Create connection pool
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,  # Auto-decode bytes to strings
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info(
                f"✓ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT} (DB {settings.REDIS_DB})"
            )

        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Token revocation disabled.",
                exc_info=True
            )
            self.redis_client = None
            self.enabled = False

    async def disconnect(self):
        """Close Redis connection and cleanup resources."""
        if self.redis_client:
            try:
                await self.redis_client.aclose()
                logger.info("✓ Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Cache key

        Returns:
            Value if exists, None otherwise
        """
        if not self.redis_client or not self.enabled:
            return None

        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis with optional TTL.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client or not self.enabled:
            return False

        try:
            if ttl:
                await self.redis_client.setex(key, ttl, value)
            else:
                await self.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Cache key to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.redis_client or not self.enabled:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.redis_client or not self.enabled:
            return False

        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False

    async def ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Seconds remaining, -1 if no expiration, -2 if key doesn't exist
        """
        if not self.redis_client or not self.enabled:
            return None

        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return None

    # Token blacklist specific methods

    async def blacklist_token(self, token: str, ttl: int) -> bool:
        """
        Blacklist a JWT token (for logout).

        Args:
            token: JWT token string
            ttl: Time until token would expire naturally (seconds)

        Returns:
            True if blacklisted, False if Redis unavailable

        Usage:
            # When user logs out:
            from app.core.security import extract_token_data

            payload = extract_token_data(token)
            exp = payload.get("exp")
            now = datetime.utcnow().timestamp()
            ttl = int(exp - now)

            await cache.blacklist_token(token, ttl)
        """
        key = f"blacklist:token:{token}"
        return await self.set(key, "1", ttl=ttl)

    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if JWT token is blacklisted.

        Args:
            token: JWT token string

        Returns:
            True if blacklisted, False otherwise

        Usage:
            # In authentication dependency:
            if await cache.is_token_blacklisted(token):
                raise HTTPException(401, "Token has been revoked")
        """
        key = f"blacklist:token:{token}"
        return await self.exists(key)


# Global instance
_redis_cache: Optional[RedisCache] = None


async def get_redis_cache() -> RedisCache:
    """
    Get Redis cache singleton instance.

    Returns:
        RedisCache: Global Redis cache instance

    Usage:
        cache = await get_redis_cache()
        await cache.set("key", "value")
    """
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
        await _redis_cache.connect()
    return _redis_cache


async def close_redis_cache():
    """
    Close Redis connection.

    Call this during application shutdown.
    """
    global _redis_cache
    if _redis_cache:
        await _redis_cache.disconnect()
        _redis_cache = None

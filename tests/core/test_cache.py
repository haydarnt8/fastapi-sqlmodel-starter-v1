"""
Tests for Redis Cache Module
"""

import pytest
from app.core.cache import get_redis_cache

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = await get_redis_cache()
    await cache.set("test_key", "test_value", ttl=60)
    value = await cache.get("test_key")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_token_blacklist():
    cache = await get_redis_cache()
    token = "test-token"
    await cache.blacklist_token(token, ttl=60)
    is_blacklisted = await cache.is_token_blacklisted(token)
    assert is_blacklisted

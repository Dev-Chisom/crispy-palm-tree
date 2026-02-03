"""Redis caching service."""

import json
import redis
from typing import Optional, Any
from datetime import timedelta
from app.config import settings


class CacheService:
    """Service for Redis caching operations."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            serialized = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False


# Global cache instance
cache_service = CacheService()

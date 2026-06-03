import hashlib
import json
from typing import Any
import redis.asyncio as redis
from app.config import settings
import structlog

logger = structlog.get_logger()

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def generate_cache_key(self, *args) -> str:
        """
        Generates a deterministic MD5 hash key from any number of arguments.
        Useful for complex caching configurations.
        """
        str_args = []
        for arg in args:
            if isinstance(arg, (dict, list)):
                str_args.append(json.dumps(arg, sort_keys=True, default=str))
            else:
                str_args.append(str(arg))
                
        raw_key = ":".join(str_args)
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

    async def get(self, key: str) -> Any | None:
        try:
            val = await self.redis_client.get(key)
            if val:
                return json.loads(val)
            return None
        except Exception as e:
            logger.error("Failed to get key from redis", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error("Failed to set key in redis", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error("Failed to delete key from redis", key=key, error=str(e))

cache_service = CacheService()

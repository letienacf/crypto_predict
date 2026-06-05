import json

import redis.asyncio as aioredis


class RedisEventBus:
    """Thin Redis pub/sub wrapper with explicit lifecycle."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)

    async def publish(self, channel: str, payload: dict) -> None:
        if self._redis is None:
            raise RuntimeError("RedisEventBus is not connected")
        await self._redis.publish(channel, json.dumps(payload, separators=(",", ":")))

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

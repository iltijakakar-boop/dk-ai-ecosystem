from typing import Optional

import redis.asyncio as aioredis
from fastapi import Request


async def get_redis(request: Request) -> Optional[aioredis.Redis]:
    """
    FastAPI dependency that returns the active Redis client connection
    stored in the FastAPI app state.
    """
    return getattr(request.app.state, "redis_client", None)

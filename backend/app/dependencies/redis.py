from fastapi import Request
import redis.asyncio as aioredis
from typing import Optional

async def get_redis(request: Request) -> Optional[aioredis.Redis]:
    """
    FastAPI dependency that returns the active Redis client connection
    stored in the FastAPI app state.
    """
    return getattr(request.app.state, "redis_client", None)

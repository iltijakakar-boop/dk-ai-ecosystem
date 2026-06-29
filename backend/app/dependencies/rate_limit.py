from fastapi import Depends, HTTPException, Request, status
import redis.asyncio as aioredis
from typing import Optional
from app.dependencies.redis import get_redis
from app.core.logging import logger

async def login_rate_limiter(
    request: Request,
    redis_client: Optional[aioredis.Redis] = Depends(get_redis)
) -> None:
    """
    Enforces a rate limit of 5 login attempts per 5 minutes per client IP.
    """
    if not redis_client:
        logger.warning("Redis is not online. Skipping login rate limit checks.")
        return

    client_ip = request.client.host if request.client else "unknown_ip"
    key = f"rate_limit:login:{client_ip}"

    try:
        attempts = await redis_client.get(key)
        if attempts and int(attempts) >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts from this IP. Please try again in 5 minutes."
            )
        
        # Increment attempts and set expiration to 5 minutes
        pipe = redis_client.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, 300)  # 5 minutes
        await pipe.execute()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limiting checks encountered an error: {e}")
        return

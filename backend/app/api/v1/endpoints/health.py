import platform
import time
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis.asyncio as aioredis
from typing import Optional

from app.dependencies.db import get_db
from app.dependencies.redis import get_redis
from app.config.settings import settings

router = APIRouter()

@router.get("", response_model=dict)
async def health_check(
    request: Request,
    db: Session = Depends(get_db),
    redis_client: Optional[aioredis.Redis] = Depends(get_redis)
):
    # Database status check
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass
    
    # Redis status check
    redis_status = "disconnected"
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_status = "connected"
        except Exception:
            pass

    # Calculate uptime
    start_time = getattr(request.app.state, "start_time", None)
    if start_time:
        uptime_seconds = time.time() - start_time
    else:
        uptime_seconds = 0.0
    uptime_str = f"{uptime_seconds:.2f} seconds"

    return {
        "application": "healthy",
        "database": db_status,
        "redis": redis_status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime": uptime_str,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "api_version": "v1"
    }

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis
from app.core.logging import setup_logging, logger
from app.config.settings import settings
from app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Logging based on environment
    setup_logging(settings.ENVIRONMENT)
    logger.info("Initializing DK AI Ecosystem backend services...")
    
    # Record startup time
    app.state.start_time = time.time()

    # Database engine verification and initialization
    try:
        with engine.connect() as conn:
            logger.info("Successfully connected to the Database.")
            app.state.db_connected = True
        
        # Run DB initialization and seed superuser
        from app.db.session import SessionLocal
        from app.db.init_db import init_db
        db = SessionLocal()
        try:
            init_db(db)
            logger.info("Database tables initialized and seeded successfully.")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to connect to or initialize the Database: {e}")
        app.state.db_connected = False

    # Redis connection pool initialization
    try:
        app.state.redis_client = aioredis.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0
        )
        await app.state.redis_client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        app.state.redis_client = None

    yield

    # Graceful shutdown
    logger.info("Shutting down resources...")
    if hasattr(app.state, "redis_client") and app.state.redis_client:
        await app.state.redis_client.aclose()
        logger.info("Redis connection closed.")
    
    engine.dispose()
    logger.info("Database engine connections disposed.")

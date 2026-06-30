import time
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.config.settings import settings
from app.core.logging import logger, setup_logging
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
        with engine.connect():
            logger.info("Successfully connected to the Database.")
            app.state.db_connected = True

        # Run DB initialization and seed superuser
        from app.db.init_db import init_db
        from app.db.session import SessionLocal

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
            socket_timeout=2.0,
        )
        await app.state.redis_client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        app.state.redis_client = None

    # Discover and load cognitive AI agents
    try:
        from ai.core.agent_manager import agent_manager

        agent_manager.discover_agents()
        logger.info(
            f"Successfully loaded agents on startup: {[a['id'] for a in agent_manager.list_agents()]}"
        )
    except Exception as e:
        logger.error(f"Failed to discover and register agents on startup: {e}")

    # Discover and load tools and plugins
    try:
        from ai.tools.tool_registry import tool_registry
        from plugins.runtime.plugin_loader import plugin_loader

        tool_registry.discover_builtin_tools()
        plugin_loader.discover_and_load_plugins()
        logger.info(
            f"Successfully loaded tools on startup: {[t['tool_id'] for t in tool_registry.list_tools()]}"
        )
    except Exception as e:
        logger.error(f"Failed to discover and register tools on startup: {e}")

    # Start task queue background workers
    try:
        from app.services.task_queue import task_queue

        task_queue.start()
    except Exception as e:
        logger.error(f"Failed to start task queue: {e}")

    # Start scheduled automation recovery
    try:
        from app.db.session import SessionLocal
        from app.services.automation_service import automation_service
        from app.services.scheduler_service import scheduler_service

        scheduler_service.start(
            db_session_factory=SessionLocal,
            execute_callback=automation_service.enqueue_scheduled_job,
        )
    except Exception as e:
        logger.error(f"Failed to start automation scheduler: {e}")

    yield

    # Graceful shutdown
    logger.info("Shutting down resources...")

    # Stop scheduler and task queue
    try:
        from app.services.scheduler_service import scheduler_service

        scheduler_service.stop()
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

    try:
        from app.services.task_queue import task_queue

        await task_queue.stop()
    except Exception as e:
        logger.error(f"Error stopping task queue: {e}")

    if hasattr(app.state, "redis_client") and app.state.redis_client:
        await app.state.redis_client.aclose()
        logger.info("Redis connection closed.")

    engine.dispose()
    logger.info("Database engine connections disposed.")

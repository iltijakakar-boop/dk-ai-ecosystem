import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.dependencies.db import get_db
from app.monitoring.agent_metrics import get_agent_metrics
from app.monitoring.cleanup import cleanup_expired_metrics_and_logs
from app.monitoring.metrics import metrics_registry
from app.monitoring.plugin_metrics import get_plugin_metrics
from app.monitoring.system import get_system_metrics
from app.monitoring.tool_metrics import get_tool_metrics
from app.schemas.response import APIResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", response_model=APIResponse[Dict[str, Any]])
async def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Returns the live status of backend dependencies (SQLite/PostgreSQL and Redis).
    """
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check: Database failure: {e}")

    redis_ok = False
    redis_client = getattr(request.app.state, "redis_client", None)
    if redis_client:
        try:
            # redis client might be async, handle ping
            import inspect

            res = redis_client.ping()
            if inspect.isawaitable(res):
                await res
            redis_ok = True
        except Exception as e:
            logger.error(f"Health check: Redis failure: {e}")

    is_healthy = db_ok
    status = (
        "healthy" if (db_ok and redis_ok) else ("degraded" if db_ok else "unhealthy")
    )
    return APIResponse(
        success=is_healthy,
        data={
            "database": "healthy" if db_ok else "unhealthy",
            "redis": "healthy" if redis_ok else "unhealthy",
            "status": status,
        },
        message="System health status retrieved successfully.",
    )


@router.get("/system", response_model=APIResponse[Dict[str, Any]])
def get_system_telemetry():
    """
    Returns active hardware CPU, memory, disk usage, uptime, and process connection counts.
    """
    try:
        sys_data = get_system_metrics()
        return APIResponse(success=True, data=sys_data)
    except Exception as e:
        return APIResponse(
            success=False, error=str(e), message="Failed to retrieve system metrics."
        )


@router.get("/metrics", response_model=APIResponse[Dict[str, Any]])
def get_api_metrics():
    """
    Returns memory-aggregated API request counters and database metrics.
    """
    data = {
        "total_requests": metrics_registry.total_requests,
        "error_count": metrics_registry.error_count,
        "auth_failures": metrics_registry.auth_failures,
        "database_queries": metrics_registry.db_queries,
        "redis_operations": metrics_registry.redis_operations,
        "average_response_time_ms": metrics_registry.get_average_response_time(),
    }
    return APIResponse(success=True, data=data)


@router.get("/agents", response_model=APIResponse[Dict[str, Any]])
def get_agent_telemetry():
    """
    Returns database-aggregated metrics for agent executions, failures, and model/provider usages.
    """
    data = get_agent_metrics()
    return APIResponse(success=True, data=data)


@router.get("/tools", response_model=APIResponse[Dict[str, Any]])
def get_tool_telemetry():
    """
    Returns database-aggregated metrics for tool calls, execution durations, and timeouts.
    """
    data = get_tool_metrics()
    return APIResponse(success=True, data=data)


@router.get("/plugins", response_model=APIResponse[Dict[str, Any]])
def get_plugin_telemetry():
    """
    Returns installed, active, disabled, and failed plugin statistics.
    """
    data = get_plugin_metrics()
    return APIResponse(success=True, data=data)


@router.get("/logs", response_model=APIResponse[Dict[str, Any]])
def tail_application_logs():
    """
    Tails the recent lines written to the local rotating log file (app.log).
    """
    log_file = os.path.abspath(os.path.join("logs", "app.log"))
    if not os.path.exists(log_file):
        return APIResponse(
            success=False,
            error="Log file not found.",
            message="Ensure ENABLE_FILE_LOGGING is enabled in settings to write to disk.",
        )

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Read last 100 lines safely
            lines = f.readlines()
            tail_lines = lines[-100:]
        return APIResponse(
            success=True,
            data={"lines": [line.strip() for line in tail_lines]},
            message=f"Retrieved last {len(tail_lines)} lines of application logs.",
        )
    except Exception as e:
        return APIResponse(
            success=False, error=str(e), message="Failed to read application log files."
        )


@router.post("/cleanup", response_model=APIResponse[Dict[str, Any]])
def trigger_retention_cleanup():
    """
    Trigger manual purge of expired system metrics and execution audit logs.
    """
    res = cleanup_expired_metrics_and_logs()
    if not res["success"]:
        return APIResponse(
            success=False, error=res.get("error"), message="Retention cleanup failed."
        )
    return APIResponse(
        success=True, data=res, message="Retention cleanup executed successfully."
    )

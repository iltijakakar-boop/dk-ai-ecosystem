from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.config.settings import settings
from app.core.logging.logger import logger
from app.db.session import SessionLocal
from app.models.monitoring_model import SystemMetric, ExecutionMetric
from app.models.tool_model import ToolExecutionLog

def cleanup_expired_metrics_and_logs() -> Dict[str, Any]:
    """
    Scheduled retention cleanup service task. Purges expired metrics and execution logs
    according to METRICS_RETENTION_DAYS and LOG_RETENTION_DAYS settings.
    """
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    
    # Calculate cutoff limits
    metrics_cutoff = now - timedelta(days=settings.METRICS_RETENTION_DAYS)
    logs_cutoff = now - timedelta(days=settings.LOG_RETENTION_DAYS)

    deleted_sys = 0
    deleted_exec = 0
    deleted_logs = 0

    try:
        # 1. Purge expired system metrics
        deleted_sys = db.query(SystemMetric).filter(SystemMetric.timestamp < metrics_cutoff).delete()
        
        # 2. Purge expired execution metrics
        deleted_exec = db.query(ExecutionMetric).filter(ExecutionMetric.timestamp < metrics_cutoff).delete()
        
        # 3. Purge expired tool execution logs
        deleted_logs = db.query(ToolExecutionLog).filter(ToolExecutionLog.created_at < logs_cutoff).delete()
        
        db.commit()
        logger.info(
            f"Metrics cleanup completed: deleted {deleted_sys + deleted_exec} metrics rows, "
            f"and {deleted_logs} tool execution log entries."
        )
        return {
            "success": True,
            "deleted_system_metrics": deleted_sys,
            "deleted_execution_metrics": deleted_exec,
            "deleted_tool_logs": deleted_logs
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to execute metrics cleanup database operations: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()

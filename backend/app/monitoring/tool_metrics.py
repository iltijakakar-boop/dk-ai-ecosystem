from typing import Any, Dict

from sqlalchemy.sql import func

from app.db.session import SessionLocal
from app.models.tool_model import ToolExecutionLog


def get_tool_metrics() -> Dict[str, Any]:
    """
    Queries the database tool_execution_logs table to gather analytics.
    """
    db = SessionLocal()
    try:
        total = db.query(func.count(ToolExecutionLog.id)).scalar() or 0
        successes = (
            db.query(func.count(ToolExecutionLog.id))
            .filter(ToolExecutionLog.status == "success")
            .scalar()
            or 0
        )
        failures = total - successes

        avg_duration = db.query(func.avg(ToolExecutionLog.duration_ms)).scalar() or 0.0

        # Count logs with timeout error signatures
        timeouts = (
            db.query(func.count(ToolExecutionLog.id))
            .filter(ToolExecutionLog.error.like("%timeout%"))
            .scalar()
            or 0
        )

        success_rate = (successes / total * 100.0) if total > 0 else 0.0

        return {
            "total_executions": total,
            "successes": successes,
            "failures": failures,
            "success_rate": success_rate,
            "average_duration_ms": float(avg_duration),
            "timeout_count": timeouts,
        }
    except Exception:
        return {
            "total_executions": 0,
            "successes": 0,
            "failures": 0,
            "success_rate": 0.0,
            "average_duration_ms": 0.0,
            "timeout_count": 0,
        }
    finally:
        db.close()

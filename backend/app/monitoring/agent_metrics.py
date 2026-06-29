from typing import Any, Dict

from sqlalchemy import Integer, cast
from sqlalchemy.sql import func

from app.db.session import SessionLocal
from app.models.monitoring_model import ExecutionMetric


def get_agent_metrics() -> Dict[str, Any]:
    """
    Queries the database execution_metrics table to compute agent performance metrics.
    """
    db = SessionLocal()
    try:
        # Query total count, success sum, and average duration for agent runs
        query = (
            db.query(
                func.count(ExecutionMetric.id).label("total"),
                func.sum(cast(ExecutionMetric.success, Integer)).label("successes"),
                func.avg(ExecutionMetric.execution_time).label("avg_latency"),
            )
            .filter(ExecutionMetric.component.like("agent:%"))
            .first()
        )

        total = query.total or 0
        successes = query.successes or 0
        failures = total - successes
        avg_latency = float(query.avg_latency or 0.0)
        success_rate = (successes / total * 100.0) if total > 0 else 0.0

        # Placeholder usage distributions (to be extended when providers log keys)
        provider_usage = {"gemini": successes, "openai": 0}
        model_usage = {"gemini-2.5-flash": total}

        return {
            "total_executions": total,
            "successes": successes,
            "failures": failures,
            "success_rate": success_rate,
            "average_latency_ms": avg_latency,
            "token_usage_placeholder": 0,
            "provider_usage": provider_usage,
            "model_usage": model_usage,
        }
    except Exception:
        # Fallback metrics in case tables are uninitialized
        return {
            "total_executions": 0,
            "successes": 0,
            "failures": 0,
            "success_rate": 0.0,
            "average_latency_ms": 0.0,
            "token_usage_placeholder": 0,
            "provider_usage": {},
            "model_usage": {},
        }
    finally:
        db.close()

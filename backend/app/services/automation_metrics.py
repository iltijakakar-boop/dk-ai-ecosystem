from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.automation import AutomationJob, JobExecution
from app.services.task_queue import task_queue


class AutomationMetricsService:
    """
    Accumulates statistics for the AI Automation & Task Execution dashboard.
    """

    def get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        # Basic counts
        total_jobs = db.query(AutomationJob).count()
        enabled_jobs = db.query(AutomationJob).filter(AutomationJob.enabled).count()
        scheduled_jobs = (
            db.query(AutomationJob)
            .filter(
                AutomationJob.enabled,
                AutomationJob.trigger_type.in_(["cron", "interval"]),
            )
            .count()
        )

        # Executions statistics
        total_executions = db.query(JobExecution).count()
        completed_executions = (
            db.query(JobExecution).filter(JobExecution.status == "Completed").count()
        )
        failed_executions = (
            db.query(JobExecution).filter(JobExecution.status == "Failed").count()
        )
        running_executions = (
            db.query(JobExecution).filter(JobExecution.status == "Running").count()
        )

        # Today's executions
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        todays_executions = (
            db.query(JobExecution)
            .filter(JobExecution.started_at >= today_start)
            .count()
        )

        # Retry statistics
        total_retries = db.query(func.sum(JobExecution.retry_count)).scalar() or 0

        # Success/Failure Rates
        success_rate = 0.0
        failure_rate = 0.0
        finished_executions = completed_executions + failed_executions
        if finished_executions > 0:
            success_rate = round((completed_executions / finished_executions) * 100, 2)
            failure_rate = round((failed_executions / finished_executions) * 100, 2)

        # Average duration calculation (completed jobs)
        avg_duration = (
            db.query(func.avg(JobExecution.duration_ms))
            .filter(JobExecution.status == "Completed")
            .scalar()
            or 0.0
        )
        avg_duration_ms = round(float(avg_duration), 2)

        # Event trigger count
        event_trigger_count = (
            db.query(JobExecution)
            .filter(JobExecution.trigger_source == "event")
            .count()
        )

        # Live queue & worker state
        queue_size = task_queue.get_queue_size()
        active_workers = task_queue.get_active_workers_count()

        # Build stats payload
        return {
            "total_jobs": total_jobs,
            "enabled_jobs": enabled_jobs,
            "scheduled_jobs": scheduled_jobs,
            "running_jobs": running_executions,
            "queue_size": queue_size,
            "active_workers": active_workers,
            "failed_jobs": failed_executions,
            "retry_count": total_retries,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_execution_time_ms": avg_duration_ms,
            "todays_executions_count": todays_executions,
            "event_trigger_count": event_trigger_count,
            "total_executions": total_executions,
        }


automation_metrics = AutomationMetricsService()

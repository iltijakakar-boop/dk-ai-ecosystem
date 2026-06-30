import asyncio
from datetime import datetime, timezone
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.core.logging import logger
from app.models.automation import AutomationJob, JobExecution


class APSchedulerService:
    """
    APScheduler abstraction layer for scheduled job management and state recovery.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=settings.DEFAULT_TIMEZONE)
        self._is_running = False

    def start(
        self,
        db_session_factory: Callable[[], Session],
        execute_callback: Callable[[int], None],
    ):
        if not settings.ENABLE_SCHEDULER:
            logger.info("Scheduler is disabled in configuration settings.")
            return

        if self._is_running:
            return

        self._is_running = True
        self.scheduler.start()
        logger.info("APScheduler AsyncIOScheduler started successfully.")

        # Recover scheduled jobs and executions
        db = db_session_factory()
        try:
            self.recover_scheduler(db, db_session_factory, execute_callback)
        finally:
            db.close()

    def stop(self):
        if not self._is_running:
            return
        self._is_running = False
        self.scheduler.shutdown()
        logger.info("APScheduler AsyncIOScheduler stopped.")

    def add_scheduled_job(
        self,
        job_id: int,
        trigger_type: str,
        cron_expr: Optional[str],
        interval_secs: Optional[int],
        execute_callback: Callable[[int], None],
    ):
        """
        Adds a scheduled job to APScheduler.
        """
        if not self._is_running:
            return

        def job_func():
            return asyncio.create_task(self._safe_execute_job(job_id, execute_callback))

        job_key = f"job_{job_id}"

        # Remove existing if any
        self.remove_scheduled_job(job_id)

        try:
            if trigger_type == "cron" and cron_expr:
                self.scheduler.add_job(
                    job_func,
                    CronTrigger.from_crontab(cron_expr),
                    id=job_key,
                    max_instances=1,
                    replace_existing=True,
                )
                logger.info(
                    f"Registered Cron Job {job_id} with expression '{cron_expr}'."
                )
            elif trigger_type == "interval" and interval_secs:
                self.scheduler.add_job(
                    job_func,
                    IntervalTrigger(seconds=interval_secs),
                    id=job_key,
                    max_instances=1,
                    replace_existing=True,
                )
                logger.info(
                    f"Registered Interval Job {job_id} running every {interval_secs}s."
                )
            else:
                logger.warning(
                    f"Unable to schedule Job {job_id}: Invalid trigger definition."
                )
        except Exception as e:
            logger.exception(f"Failed to register scheduled Job {job_id}: {e}")

    def remove_scheduled_job(self, job_id: int):
        job_key = f"job_{job_id}"
        if self.scheduler.get_job(job_key):
            self.scheduler.remove_job(job_key)
            logger.info(f"Removed Job {job_id} from APScheduler registry.")

    async def _safe_execute_job(
        self, job_id: int, execute_callback: Callable[[int], None]
    ):
        try:
            # Execute callback (which enqueues it to PriorityTaskQueue)
            execute_callback(job_id)
        except Exception as e:
            logger.error(f"Error triggering scheduled Job {job_id}: {e}")

    def recover_scheduler(
        self,
        db: Session,
        db_session_factory: Callable[[], Session],
        execute_callback: Callable[[int], None],
    ):
        """
        Loads enabled jobs on startup, cleans up running/interrupted job execution statuses.
        """
        # 1. Clean up interrupted executions (Running/Queued/Pending)
        interrupted_executions = (
            db.query(JobExecution)
            .filter(
                JobExecution.status.in_(
                    ["Pending", "Queued", "Running", "Waiting", "Retrying"]
                )
            )
            .all()
        )

        for exec_obj in interrupted_executions:
            exec_obj.status = "Failed"
            exec_obj.completed_at = datetime.now(timezone.utc)
            exec_obj.error = (
                "Ecosystem restart: Execution interrupted during system reboot."
            )
            logger.warning(
                f"Recovered interrupted Execution {exec_obj.execution_uuid} "
                f"(Job {exec_obj.job_id}): marked as Failed."
            )
        db.commit()

        # 2. Reload scheduled jobs
        jobs = db.query(AutomationJob).filter(AutomationJob.enabled).all()
        for job in jobs:
            if job.trigger_type in ["cron", "interval"]:
                self.add_scheduled_job(
                    job_id=job.id,
                    trigger_type=job.trigger_type,
                    cron_expr=job.cron_expression,
                    interval_secs=job.interval_seconds,
                    execute_callback=execute_callback,
                )

        logger.info(f"Scheduler recovery complete. Reloaded {len(jobs)} enabled jobs.")


scheduler_service = APSchedulerService()

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.automation import JobExecution, JobExecutionLog


class ExecutionHistoryManager:
    """
    Manages database state persistence for automation executions and detailed logs.
    """

    def create_execution(
        self,
        db: Session,
        job_id: int,
        execution_uuid: str,
        trigger_source: str,
        status: str = "Pending",
    ) -> JobExecution:
        db_obj = JobExecution(
            job_id=job_id,
            execution_uuid=execution_uuid,
            status=status,
            trigger_source=trigger_source,
            started_at=datetime.utcnow(),
            retry_count=0,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        self.log_step(
            db, execution_uuid, "INFO", f"Execution initialized via {trigger_source}."
        )
        return db_obj

    def update_execution(
        self,
        db: Session,
        execution_uuid: str,
        status: str,
        duration_ms: Optional[int] = None,
        retry_count: int = 0,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[JobExecution]:
        exec_obj = (
            db.query(JobExecution)
            .filter(JobExecution.execution_uuid == execution_uuid)
            .first()
        )
        if not exec_obj:
            return None

        exec_obj.status = status
        exec_obj.retry_count = retry_count
        if duration_ms is not None:
            exec_obj.duration_ms = duration_ms
        if result is not None:
            exec_obj.result = result
        if error is not None:
            exec_obj.error = error

        if status in ["Completed", "Failed", "Cancelled"]:
            exec_obj.completed_at = datetime.utcnow()
            if exec_obj.started_at:
                delta = exec_obj.completed_at - exec_obj.started_at
                exec_obj.duration_ms = int(delta.total_seconds() * 1000)

        db.commit()
        db.refresh(exec_obj)

        lvl = "INFO" if status == "Completed" else "ERROR"
        msg = f"Execution transitioned to: {status}."
        self.log_step(db, execution_uuid, lvl, msg)
        return exec_obj

    def log_step(
        self,
        db: Session,
        execution_uuid: str,
        level: str,
        message: str,
        duration_ms: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> JobExecutionLog:
        log_obj = JobExecutionLog(
            execution_uuid=execution_uuid,
            timestamp=datetime.utcnow(),
            level=level.upper(),
            message=message,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
        )
        db.add(log_obj)
        db.commit()
        db.refresh(log_obj)
        return log_obj

    def get_logs(self, db: Session, execution_uuid: str) -> List[JobExecutionLog]:
        return (
            db.query(JobExecutionLog)
            .filter(JobExecutionLog.execution_uuid == execution_uuid)
            .order_by(JobExecutionLog.timestamp.asc())
            .all()
        )

    def get_job_executions(
        self, db: Session, job_id: int, limit: int = 50
    ) -> List[JobExecution]:
        return (
            db.query(JobExecution)
            .filter(JobExecution.job_id == job_id)
            .order_by(JobExecution.started_at.desc())
            .limit(limit)
            .all()
        )


execution_history = ExecutionHistoryManager()

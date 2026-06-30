import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class AutomationJob(Base):
    """
    SQLAlchemy model representing an AI automation job.
    """

    __tablename__ = "automation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    trigger_type = Column(
        String, index=True, nullable=False
    )  # cron, interval, event, manual, webhook
    cron_expression = Column(String, nullable=True)
    interval_seconds = Column(Integer, nullable=True)
    workflow_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=True)
    variables = Column(
        String, default="{}", nullable=False
    )  # JSON-serialized variables dictionary
    priority = Column(
        String, default="NORMAL", nullable=False
    )  # LOW, NORMAL, HIGH, CRITICAL
    depends_on_job_id = Column(Integer, ForeignKey("automation_jobs.id"), nullable=True)
    dependency_status = Column(String, default="completed", nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Self-referencing relationship for dependencies
    dependencies = relationship("AutomationJob", remote_side=[id])


class JobExecution(Base):
    """
    SQLAlchemy model tracking job execution histories.
    """

    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("automation_jobs.id"), nullable=False)
    execution_uuid = Column(
        String,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    status = Column(String, index=True, default="Pending", nullable=False)
    trigger_source = Column(
        String, index=True, nullable=False
    )  # scheduler, event, manual, webhook
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    result = Column(String, nullable=True)  # JSON-serialized result payload
    error = Column(String, nullable=True)

    job = relationship("AutomationJob", backref="executions")


class JobExecutionLog(Base):
    """
    SQLAlchemy model tracking step-by-step logs for a specific execution.
    """

    __tablename__ = "job_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_uuid = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    level = Column(String, default="INFO", nullable=False)  # INFO, WARNING, ERROR
    message = Column(String, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    correlation_id = Column(String, nullable=True)


class Notification(Base):
    """
    SQLAlchemy model tracking notifications sent during automation runs.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # email, webhook, slack, discord, teams
    recipient = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    message = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, sent, failed
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

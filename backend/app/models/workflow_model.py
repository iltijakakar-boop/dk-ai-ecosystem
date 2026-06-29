from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from app.db.session import Base

class Workflow(Base):
    """
    SQLAlchemy model tracking workflow templates and versions.
    """
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, index=True, nullable=False) # Logical identifier across versions
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False) # Distinguishes seeded templates
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    definition = Column(String, nullable=False) # JSON-serialized steps and routing rules
    created_at = Column(DateTime, default=func.now(), nullable=False)


class WorkflowExecution(Base):
    """
    SQLAlchemy model tracking runtime execution progress of a workflow template.
    """
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, running, waiting, completed, failed, cancelled
    current_step = Column(String, nullable=True)
    context = Column(String, default="{}", nullable=False) # JSON-serialized shared variables context
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", backref="executions")


class Task(Base):
    """
    SQLAlchemy model representing individual task nodes in an execution pipeline.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, running, waiting, completed, failed, cancelled
    required_capability = Column(String, nullable=True)       # e.g. coding, research, document
    input_data = Column(String, default="{}", nullable=False)  # JSON input
    output_data = Column(String, nullable=True)                # JSON output
    error = Column(String, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    timeout_seconds = Column(Integer, default=60, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    execution = relationship("WorkflowExecution", backref=backref("tasks", cascade="all, delete-orphan", passive_deletes=True))


class TaskExecution(Base):
    """
    SQLAlchemy model auditing specific execution logs of a task by an allocated agent.
    """
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, nullable=False)
    status = Column(String, nullable=False) # running, completed, failed
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    log = Column(String, nullable=True)

    # Relationships
    task = relationship("Task", backref=backref("task_executions", cascade="all, delete-orphan", passive_deletes=True))


class AgentAssignment(Base):
    """
    SQLAlchemy model tracking dynamic task allocation to collaborating agents.
    """
    __tablename__ = "agent_assignments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, nullable=False)
    assigned_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    task = relationship("Task", backref=backref("assignments", cascade="all, delete-orphan", passive_deletes=True))


class WorkflowLog(Base):
    """
    SQLAlchemy model tracking event bus state audits.
    """
    __tablename__ = "workflow_logs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String, nullable=False) # AgentStarted, AgentFinished, TaskCreated, TaskCompleted, etc.
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    execution = relationship("WorkflowExecution", backref=backref("logs", cascade="all, delete-orphan", passive_deletes=True))


class DeadLetterQueue(Base):
    """
    SQLAlchemy model holding exhausted failures diagnostics.
    """
    __tablename__ = "dead_letter_queue"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    failure_reason = Column(String, nullable=False)
    retry_count = Column(Integer, nullable=False)
    stack_trace = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    task = relationship("Task", backref=backref("dlq_entries", cascade="all, delete-orphan", passive_deletes=True))
    execution = relationship("WorkflowExecution", backref=backref("dlq_entries", cascade="all, delete-orphan", passive_deletes=True))

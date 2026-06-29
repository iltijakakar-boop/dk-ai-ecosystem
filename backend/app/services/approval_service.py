import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ai.orchestrator.event_bus import event_bus
from sqlalchemy.orm import Session

from app.models.workflow_model import DeadLetterQueue, Task, WorkflowExecution


class ApprovalService:
    """
    Coordinates human-in-the-loop operations: resolves approval requests,
    marks suspended nodes as completed, or moves rejected runs to the Dead Letter Queue.
    """

    def approve_task(
        self,
        db: Session,
        task_id: int,
        override_output: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Approves a suspended task, marks it completed, and resumes execution.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != "waiting":
            return False

        exec_obj = (
            db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == task.workflow_execution_id)
            .first()
        )
        if not exec_obj:
            return False

        # 1. Complete task details
        task.status = "completed"
        task.output_data = json.dumps(
            override_output
            or {"status": "approved", "comment": "Approved by human operator"}
        )

        # 2. Reset execution status to running
        exec_obj.status = "running"
        db.commit()

        # Log event logs
        event_bus.publish(
            exec_obj.id,
            task.id,
            "TaskCompleted",
            f"Task '{task.name}' approved and completed by human operator.",
        )
        return True

    def reject_task(
        self, db: Session, task_id: int, reason: str = "Rejected by human operator"
    ) -> bool:
        """
        Rejects a suspended task, marks it failed, halts the pipeline, and moves it to DLQ.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != "waiting":
            return False

        exec_obj = (
            db.query(WorkflowExecution)
            .filter(WorkflowExecution.id == task.workflow_execution_id)
            .first()
        )
        if not exec_obj:
            return False

        # 1. Mark task and execution as failed
        task.status = "failed"
        task.error = reason
        exec_obj.status = "failed"
        exec_obj.completed_at = datetime.now(timezone.utc)

        # 2. Move to Dead Letter Queue (DLQ)
        dlq_entry = DeadLetterQueue(
            task_id=task.id,
            workflow_execution_id=exec_obj.id,
            failure_reason=f"Rejected: {reason}",
            retry_count=task.retry_count,
            stack_trace="Human Operator rejection override.",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(dlq_entry)
        db.commit()

        event_bus.publish(
            exec_obj.id,
            task.id,
            "WorkflowFailed",
            f"Task '{task.name}' rejected by human operator. Moved to DLQ.",
        )
        return True


# Global ApprovalService instance
approval_service = ApprovalService()

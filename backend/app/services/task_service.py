from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.models.workflow_model import Task


class TaskService:
    """
    Coordinates task lifecycle status updates, result registry, and errors logging.
    """

    def update_task_status(
        self,
        db: Session,
        task_id: int,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Task]:
        """
        Updates task state variables and commits modifications.
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None

        task.status = status
        if output_data is not None:
            import json

            task.output_data = json.dumps(output_data)
        if error is not None:
            task.error = error

        db.commit()
        db.refresh(task)
        logger.info(f"Updated task {task_id} status to {status}")
        return task


# Global TaskService instance
task_service = TaskService()

from typing import Dict, List, Callable, Optional
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.models.workflow_model import WorkflowLog
from app.core.logging.logger import logger


class EventBus:
    """
    In-memory Pub-Sub events dispatcher that automatically persists logs to the SQLite database.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribes a listener callback to a specific event type.
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def publish(
        self,
        workflow_execution_id: int,
        task_id: Optional[int],
        event_type: str,
        message: str,
    ) -> None:
        """
        Publishes an event, writes an audit record in the workflow_logs table,
        and triggers active subscription listener callbacks.
        """
        logger.info(
            f"[EventBus] [{event_type}] Exec: {workflow_execution_id}, Task: {task_id} - {message}"
        )

        # 1. Persist log details to database
        db = SessionLocal()
        try:
            log_record = WorkflowLog(
                workflow_execution_id=workflow_execution_id,
                task_id=task_id,
                event_type=event_type,
                message=message,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(log_record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save event log to database: {e}")
            db.rollback()
        finally:
            db.close()

        # 2. Trigger in-memory callback listeners
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(workflow_execution_id, task_id, message)
                except Exception as cb_err:
                    logger.error(f"Error executing EventBus callback: {cb_err}")


# Global EventBus instance
event_bus = EventBus()

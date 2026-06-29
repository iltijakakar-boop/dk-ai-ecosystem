import json
from typing import Dict, Any, Optional
from app.db.session import SessionLocal
from app.models.workflow_model import WorkflowExecution, Task
from app.core.logging.logger import logger

class StateManager:
    """
    Manages loading, updating, and saving execution contexts and statuses in the database.
    """
    
    @staticmethod
    def get_execution_context(execution_id: int) -> Dict[str, Any]:
        """
        Loads the shared context variables for a specific execution run.
        """
        db = SessionLocal()
        try:
            exec_obj = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
            if exec_obj and exec_obj.context:
                return json.loads(exec_obj.context)
            return {}
        finally:
            db.close()

    @staticmethod
    def update_execution_context(execution_id: int, key: str, value: Any) -> None:
        """
        Saves a new key-value pair into the execution context variables.
        """
        db = SessionLocal()
        try:
            exec_obj = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
            if exec_obj:
                ctx = json.loads(exec_obj.context) if exec_obj.context else {}
                ctx[key] = value
                exec_obj.context = json.dumps(ctx)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update context for execution {execution_id}: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def update_execution_status(execution_id: int, status: str, current_step: Optional[str] = None) -> None:
        """
        Updates the overall workflow execution state and current active step.
        """
        db = SessionLocal()
        try:
            exec_obj = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
            if exec_obj:
                exec_obj.status = status
                if current_step:
                    exec_obj.current_step = current_step
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update status for execution {execution_id}: {e}")
            db.rollback()
        finally:
            db.close()

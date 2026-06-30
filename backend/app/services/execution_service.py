import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.studio_models import ExecutionSession


class ExecutionService:
    def create_session(
        self, db: Session, *, workspace_id: int, entity_type: str, entity_id: int, inputs: Optional[Dict[str, Any]] = None
    ) -> ExecutionSession:
        session = ExecutionSession(
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status="pending",
            inputs=json.dumps(inputs or {}),
            outputs=json.dumps({}),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def execute_session_dry_run(self, db: Session, *, session_id: int) -> ExecutionSession:
        session = db.query(ExecutionSession).filter(ExecutionSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution session not found.")

        session.status = "running"
        db.commit()

        # Simulate visual flowchart execution path
        inputs = json.loads(session.inputs or "{}")
        simulated_output = {
            "result": "Execution completed successfully.",
            "echo_input": inputs,
            "tokens_used": 1200,
            "execution_path": ["start_node", "llm_generate_prompt", "agent_executor", "end_node"],
        }

        session.status = "completed"
        session.outputs = json.dumps(simulated_output)
        session.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session


execution_service = ExecutionService()

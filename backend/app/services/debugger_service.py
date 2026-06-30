import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.studio_models import DebugSession, ExecutionSession


class DebuggerService:
    def create_debug_session(self, db: Session, *, workspace_id: int, execution_session_id: Optional[int] = None) -> DebugSession:
        session = DebugSession(
            execution_session_id=execution_session_id,
            workspace_id=workspace_id,
            status="running",
            logs=json.dumps([]),
            variables_state=json.dumps({}),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_debug_session(self, db: Session, session_id: int) -> Optional[DebugSession]:
        return db.query(DebugSession).filter(DebugSession.id == session_id).first()

    def record_step_execution(
        self, db: Session, *, session_id: int, node_id: str, node_type: str, status_str: str, output_data: Dict[str, Any], variables_delta: Dict[str, Any]
    ) -> DebugSession:
        session = self.get_debug_session(db, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found.")

        # Update step logs
        current_logs = json.loads(session.logs or "[]")
        from datetime import datetime
        step_log = {
            "node_id": node_id,
            "type": node_type,
            "status": status_str,
            "output": output_data,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 150.0,
        }
        current_logs.append(step_log)
        session.logs = json.dumps(current_logs)

        # Update variable state delta
        current_vars = json.loads(session.variables_state or "{}")
        current_vars.update(variables_delta)
        session.variables_state = json.dumps(current_vars)

        session.current_step = node_id
        db.commit()
        db.refresh(session)
        return session

    def complete_debug_session(self, db: Session, *, session_id: int, status_str: str = "completed") -> DebugSession:
        session = self.get_debug_session(db, session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debug session not found.")
        session.status = status_str
        db.commit()
        db.refresh(session)
        return session


debugger_service = DebuggerService()

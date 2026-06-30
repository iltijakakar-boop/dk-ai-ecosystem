from sqlalchemy.orm import Session
from app.services.debugger_service import debugger_service


def test_visual_canvas_debugger_sessions(db: Session):
    # 1. Create debug session
    session = debugger_service.create_debug_session(db, workspace_id=1, execution_session_id=100)
    assert session.status == "running"

    # 2. Record execution step-by-step (Node A executed)
    updated_session = debugger_service.record_step_execution(
        db,
        session_id=session.id,
        node_id="node_a",
        node_type="llm",
        status_str="completed",
        output_data={"generated_text": "Greetings human"},
        variables_delta={"user_greeting": "Greetings human"}
    )
    assert updated_session.current_step == "node_a"
    assert "user_greeting" in updated_session.variables_state

    # 3. Complete Debug Session
    completed = debugger_service.complete_debug_session(db, session_id=session.id)
    assert completed.status == "completed"

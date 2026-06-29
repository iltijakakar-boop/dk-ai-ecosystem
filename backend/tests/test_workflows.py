import pytest
from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.models.workflow_model import (
    Workflow,
    WorkflowExecution,
    Task,
    DeadLetterQueue,
    WorkflowLog
)
from app.services.workflow_service import workflow_service
from ai.orchestrator.orchestrator import agent_orchestrator

@pytest.fixture(autouse=True)
def clean_workflow_database():
    """
    Purges workflow execution entries before and after each test case.
    """
    db = SessionLocal()
    try:
        db.query(DeadLetterQueue).delete()
        db.query(WorkflowLog).delete()
        db.query(Task).delete()
        db.query(WorkflowExecution).delete()
        db.query(Workflow).delete()
        db.commit()
    finally:
        db.close()
    yield


def test_workflow_templates_seeding(client: TestClient):
    """
    Verifies default system templates are seeded on DB init.
    """
    db = SessionLocal()
    try:
        workflow_service.seed_default_templates(db)
        
        # Check count of seeded templates
        templates_count = db.query(Workflow).filter(Workflow.is_template == True).count()
        assert templates_count == 4
    finally:
        db.close()


def test_workflow_versioning(client: TestClient):
    """
    Verifies that updates create a new workflow version and mark older ones inactive.
    """
    # 1. Create Version 1
    payload = {
        "workflow_id": "test_version_workflow",
        "name": "Test Versioning",
        "description": "Initial design",
        "definition": {"steps": []}
    }
    res_v1 = client.post("/api/v1/workflows", json=payload)
    assert res_v1.status_code == 200
    data_v1 = res_v1.json()["data"]
    assert data_v1["version"] == 1
    assert data_v1["is_active"] is True

    # 2. Create Version 2 (Same workflow_id)
    payload["name"] = "Test Versioning Updated"
    res_v2 = client.post("/api/v1/workflows", json=payload)
    assert res_v2.status_code == 200
    data_v2 = res_v2.json()["data"]
    assert data_v2["version"] == 2
    assert data_v2["is_active"] is True

    # 3. Check DB mapping
    db = SessionLocal()
    try:
        wfs = db.query(Workflow).filter(Workflow.workflow_id == "test_version_workflow").order_by(Workflow.version.asc()).all()
        assert len(wfs) == 2
        assert wfs[0].version == 1
        assert wfs[0].is_active is False
        assert wfs[1].version == 2
        assert wfs[1].is_active is True
    finally:
        db.close()


def test_agent_capability_matching_and_execution(client: TestClient):
    """
    Verifies orchestrator capability routing matches eligible agents.
    """
    # Seed templates
    db = SessionLocal()
    try:
        workflow_service.seed_default_templates(db)
        coding_template = db.query(Workflow).filter(Workflow.workflow_id == "coding_workflow").first()
        assert coding_template is not None
        
        # Trigger run
        exec_res = client.post(f"/api/v1/workflows/{coding_template.id}/execute")
        assert exec_res.status_code == 200
        exec_data = exec_res.json()["data"]
        
        # Wait for background threads to complete
        import time
        time.sleep(1.0)
        
        # Verify status progress
        status_res = client.get(f"/api/v1/workflows/{exec_data['id']}/status")
        assert status_res.json()["data"]["status"] == "completed"

        # Check task output references the coding agent
        tasks = db.query(Task).filter(Task.workflow_execution_id == exec_data['id']).all()
        assert len(tasks) == 2
        assert "coding_agent" in tasks[0].output_data
        assert "analysis_agent" in tasks[1].output_data or "coding_agent" in tasks[1].output_data # coding agent registers both coding/analysis
    finally:
        db.close()


def test_dead_letter_queue_on_failure(client: TestClient):
    """
    Exhausts retries on unknown capability and verifies DLQ routing.
    """
    # Create workflow requiring unsupported agent capability
    payload = {
        "workflow_id": "unsupported_workflow",
        "name": "Unsupported Workflow",
        "definition": {
            "steps": [
                {"name": "fail_step", "required_capability": "unsupported_capability", "max_retries": 1}
            ]
        }
    }
    res = client.post("/api/v1/workflows", json=payload)
    wf_id = res.json()["data"]["id"]

    # Execute
    exec_res = client.post(f"/api/v1/workflows/{wf_id}/execute")
    exec_data = exec_res.json()["data"]

    # Wait for completion
    import time
    time.sleep(1.0)

    # 1. Status should fail
    status_res = client.get(f"/api/v1/workflows/{exec_data['id']}/status")
    assert status_res.json()["data"]["status"] == "failed"

    # 2. DLQ list endpoint should record diagnostics
    dlq_res = client.get("/api/v1/workflows/dead-letter")
    assert dlq_res.status_code == 200
    dlq_data = dlq_res.json()["data"]
    assert len(dlq_data) == 1
    assert "No eligible agent found" in dlq_data[0]["failure_reason"]


def test_human_approval_pause_and_resume(client: TestClient):
    """
    Checks that human-in-the-loop task step suspends execution, which can be approved/resumed.
    """
    db = SessionLocal()
    try:
        workflow_service.seed_default_templates(db)
        review_wf = db.query(Workflow).filter(Workflow.workflow_id == "multi_agent_review_workflow").first()
        
        # Execute
        exec_res = client.post(f"/api/v1/workflows/{review_wf.id}/execute")
        exec_id = exec_res.json()["data"]["id"]

        import time
        time.sleep(1.0)

        # 1. Execution status must pause in 'waiting' state
        status_res = client.get(f"/api/v1/workflows/{exec_id}/status")
        assert status_res.json()["data"]["status"] == "waiting"

        # Resolve suspended task
        task = db.query(Task).filter(
            Task.workflow_execution_id == exec_id,
            Task.status == "waiting"
        ).first()
        assert task is not None
        assert task.name == "human_approval_step"

        # 2. Resume execution by approving task
        resume_res = client.post(f"/api/v1/workflows/{exec_id}/resume?task_id={task.id}")
        assert resume_res.status_code == 200
        
        time.sleep(1.0)

        # 3. Execution status finishes successfully
        status_res2 = client.get(f"/api/v1/workflows/{exec_id}/status")
        assert status_res2.json()["data"]["status"] == "completed"

    finally:
        db.close()

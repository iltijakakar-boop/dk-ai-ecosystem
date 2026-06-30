from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.devops_service import pipeline_service, release_service, approval_service, container_registry_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Pipeline execution
def test_pipeline_execution(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        pipe = pipeline_service.create_pipeline(session, workspace_id=1, name="production-ci-cd")
        session.commit()
        pipe_id = pipe.id
    finally:
        session.close()

    res = client.post(f"/api/v1/devops/pipelines/{pipe_id}/run", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "completed"


# 2. Release & Rollback
def test_release_rollback(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        rel1 = release_service.create_release(session, workspace_id=1, version="v1.0.0")
        session.commit()
        rel2 = release_service.create_release(session, workspace_id=1, version="v1.1.0")
        session.commit()
        rel1_id = rel1.id
        rel2_id = rel2.id
    finally:
        session.close()

    res = client.post(
        f"/api/v1/devops/rollback?workspace_id=1&current_release_id={rel2_id}&target_release_id={rel1_id}",
        headers=headers,
    )
    assert res.status_code == 200


# 3. Production Approval Gate
def test_production_approval_gate(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        rel = release_service.create_release(session, workspace_id=1, version="v2.0.0-rc")
        session.commit()
        rel_id = rel.id
    finally:
        session.close()

    res_req = client.post(f"/api/v1/devops/approvals?workspace_id=1&release_id={rel_id}", headers=headers)
    assert res_req.status_code == 200
    req_id = res_req.json()["data"]["id"]

    res_act = client.post(f"/api/v1/devops/approvals/{req_id}/action?approve=true", headers=headers)
    assert res_act.status_code == 200
    assert res_act.json()["data"]["status"] == "approved"


# 4. Artifact Versioning
def test_artifact_versioning(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/devops/registry/images",
        json={"workspace_id": 1, "name": "dk-ai-agent-core", "tag": "latest", "digest": "sha256:4a58ff01"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["tag"] == "latest"

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.studio_models import AgentStudioProject, WorkflowCanvas


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_studio_project_and_canvas_crud(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. Create Project
    proj_payload = {"workspace_id": 1, "name": "Studio Support System", "description": "Customer help agent"}
    res = client.post("/api/v1/studio/projects", json=proj_payload, headers=headers)
    assert res.status_code == 200
    proj_data = res.json()["data"]
    proj_id = proj_data["id"]
    assert proj_data["name"] == "Studio Support System"

    # 2. List Projects
    res = client.get("/api/v1/studio/projects?workspace_id=1", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0

    # 3. Create Canvas
    canvas_payload = {
        "workspace_id": 1,
        "project_id": proj_id,
        "name": "Ticket Sorting Flow",
        "description": "Sorts inbox tickets automatically",
        "definition": {"nodes": [], "edges": []},
    }
    res = client.post("/api/v1/studio/canvas", json=canvas_payload, headers=headers)
    assert res.status_code == 200
    canvas_data = res.json()["data"]
    canvas_id = canvas_data["id"]
    assert canvas_data["name"] == "Ticket Sorting Flow"

    # 4. Get Canvas Details
    res = client.get(f"/api/v1/studio/canvas/{canvas_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Ticket Sorting Flow"

    # 5. List Canvases
    res = client.get("/api/v1/studio/canvas?workspace_id=1", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0

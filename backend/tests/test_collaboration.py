from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.studio_service import studio_service
from app.schemas.studio import WorkflowCanvasCreate


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_visual_canvas_workspace_isolation_collaboration(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. User from Workspace 1 creates a canvas
    canvas_payload = {
        "workspace_id": 1,
        "name": "Secure Finance Flow",
        "description": "Sensitive financial automation data",
        "definition": {},
    }
    res = client.post("/api/v1/studio/canvas", json=canvas_payload, headers=headers)
    assert res.status_code == 200
    canvas_id = res.json()["data"]["id"]

    # 2. Try listing canvases for Workspace 2
    res_list = client.get("/api/v1/studio/canvas?workspace_id=2", headers=headers)
    assert res_list.status_code == 200
    canvases_ws2 = res_list.json()["data"]
    # Should NOT contain the canvas created in Workspace 1
    for c in canvases_ws2:
        assert c["id"] != canvas_id

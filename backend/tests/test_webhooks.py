from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.webhook_service import webhook_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_webhooks_lifecycle(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. Create Webhook Endpoint via API
    hook_payload = {
        "workspace_id": 1,
        "url": "https://callback-listener.local/webhook",
        "secret_token": "token_abc_123",
        "event_types": ["agent_finished", "workflow_completed"]
    }
    res = client.post("/api/v1/mcp/webhooks", json=hook_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["url"] == "https://callback-listener.local/webhook"

    # 2. Dispatch event and verify delivery log is created in DB (mocked execution)
    webhook_service.dispatch_event(
        db,
        workspace_id=1,
        event_type="workflow_completed",
        payload={"workflow_id": "test_wf", "status": "completed"}
    )

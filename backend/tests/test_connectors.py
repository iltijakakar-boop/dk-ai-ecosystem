from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.connector_service import connector_service
from app.services.integration_service import integration_service
from app.services.credential_service import credential_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_integration_connectors_flow(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. Create Connector via API
    conn_payload = {"workspace_id": 1, "name": "Slack Alert Channel", "type": "slack", "enabled": True}
    res = client.post("/api/v1/mcp/connectors", json=conn_payload, headers=headers)
    assert res.status_code == 200
    conn_data = res.json()["data"]
    conn_id = conn_data["id"]
    assert conn_data["name"] == "Slack Alert Channel"

    # 2. List connectors
    res_list = client.get("/api/v1/mcp/connectors?workspace_id=1", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) > 0

    # 3. Save Connector encrypted credentials
    cred_payload = {
        "workspace_id": 1,
        "connector_id": conn_id,
        "credential_data": {"token": "xoxb-mock-token-value"}
    }
    res_cred = client.post(f"/api/v1/mcp/connectors/{conn_id}/credentials", json=cred_payload, headers=headers)
    assert res_cred.status_code == 200

    # 4. Verify integration service connection
    valid = integration_service.verify_connector_connection(db, workspace_id=1, connector_id=conn_id)
    assert valid is True

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.mcp_service import mcp_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mcp_server_registration_and_heartbeat(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. Register MCP Server
    srv_payload = {"workspace_id": 1, "name": "Studio Weather Agent Server", "url": "http://localhost:5001/mcp"}
    res = client.post("/api/v1/mcp/servers", json=srv_payload, headers=headers)
    assert res.status_code == 200
    srv_data = res.json()["data"]
    srv_id = srv_data["id"]
    assert srv_data["name"] == "Studio Weather Agent Server"
    assert srv_data["status"] == "offline"

    # 2. Try list servers
    res_list = client.get("/api/v1/mcp/servers?workspace_id=1", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) > 0

    # 3. Establish connection (SSE)
    srv_payload_sse = {"workspace_id": 1, "name": "SSE Server", "url": "http://localhost:5002/mcp/sse"}
    res_sse = client.post("/api/v1/mcp/servers", json=srv_payload_sse, headers=headers)
    srv_sse_id = res_sse.json()["data"]["id"]
    
    # Establish connection mapping
    res_conn = client.post(f"/api/v1/mcp/servers/{srv_sse_id}/connect", headers=headers)
    assert res_conn.status_code == 200
    assert res_conn.json()["data"]["type"] == "sse"

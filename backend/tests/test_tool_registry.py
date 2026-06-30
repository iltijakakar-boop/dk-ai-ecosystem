from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.tool_registry_service import tool_registry_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_tool_registry_flow(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. Register REST Tool
    tool_payload = {
        "workspace_id": 1,
        "name": "fetch_weather",
        "description": "Fetches current weather for a city",
        "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}},
        "execution_type": "rest",
        "endpoint_url": "https://api.weather.com/v1",
    }
    res = client.post("/api/v1/mcp/tools", json=tool_payload, headers=headers)
    assert res.status_code == 200
    tool_data = res.json()["data"]
    tool_id = tool_data["id"]
    assert tool_data["name"] == "fetch_weather"

    # 2. List registered tools
    res_list = client.get("/api/v1/mcp/tools?workspace_id=1", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) > 0

    # 3. Direct registration service validation with dependencies
    tool = tool_registry_service.register_tool(
        db,
        workspace_id=1,
        name="send_weather_alert",
        description="Sends alert if weather is severe",
        input_schema={},
        execution_type="native",
        dependencies=["fetch_weather"]
    )
    assert tool is not None
    assert tool.name == "send_weather_alert"

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.analytics_service import analytics_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_tool_usage_analytics(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    # 1. Record mock tool calls
    session = TestingSessionLocal()
    try:
        analytics_service.record_tool_call(session, workspace_id=1, tool_name="fetch_weather", duration_ms=120.0, is_error=False)
        analytics_service.record_tool_call(session, workspace_id=1, tool_name="fetch_weather", duration_ms=180.0, is_error=True)
        session.commit()
    finally:
        session.close()

    # 2. Query stats via API
    res = client.get("/api/v1/mcp/analytics?workspace_id=1", headers=headers)
    assert res.status_code == 200
    stats = res.json()["data"]
    
    # Assert counts
    weather_stats = next(s for s in stats if s["tool_name"] == "fetch_weather")
    assert weather_stats["calls_count"] == 2
    assert weather_stats["errors_count"] == 1
    assert weather_stats["total_duration_ms"] == 300.0

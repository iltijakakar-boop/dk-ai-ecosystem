from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.observability_service import (
    metrics_service,
    logging_service,
    tracing_service,
    alert_service,
    incident_service,
)


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Metrics Collection & Alerts
def test_metrics_collection_and_alerting(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    # Seed alert rule first
    session = TestingSessionLocal()
    try:
        rule = alert_service.create_rule(session, workspace_id=1, metric_name="cpu", threshold=80.0)
        session.commit()
        rule_id = rule.id
    finally:
        session.close()

    # Record metric violating threshold to trigger alert
    res = client.post(
        "/api/v1/observability/metrics",
        json={"workspace_id": 1, "cpu_percent": 90.0, "memory_percent": 45.0},
        headers=headers,
    )
    assert res.status_code == 200

    # Query active alerts
    res_alerts = client.get("/api/v1/observability/alerts?workspace_id=1", headers=headers)
    assert res_alerts.status_code == 200
    assert len(res_alerts.json()["data"]) > 0


# 2. Log Aggregation
def test_structured_logging(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/observability/logs",
        json={"workspace_id": 1, "log_level": "WARNING", "message": "Failed API attempt"},
        headers=headers,
    )
    assert res.status_code == 200

    res_query = client.get("/api/v1/observability/logs?workspace_id=1", headers=headers)
    assert res_query.status_code == 200
    assert len(res_query.json()["data"]) > 0


# 3. Distributed Tracing
def test_distributed_tracing(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        tracing_service.create_trace(session, workspace_id=1, name="exec_agent_run", duration_ms=450.0)
        session.commit()
    finally:
        session.close()

    res = client.get("/api/v1/observability/traces?workspace_id=1", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0


# 4. Incident Response
def test_incidents_management(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/observability/incidents",
        json={"workspace_id": 1, "title": "Memory leak on node 2", "severity": "critical"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["title"] == "Memory leak on node 2"

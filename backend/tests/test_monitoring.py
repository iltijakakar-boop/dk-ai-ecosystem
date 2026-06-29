import pytest
from fastapi.testclient import TestClient
from app.monitoring.metrics import metrics_registry
from app.core.logging.logger import correlation_id_ctx

def test_request_id_middleware_and_correlation(client: TestClient):
    """
    Verifies that the RequestIDMiddleware generates, attaches,
    and returns X-Correlation-ID headers for ASGI requests.
    """
    res = client.get("/api/v1/monitoring/health")
    assert res.status_code == 200
    
    # Check headers
    assert "X-Correlation-ID" in res.headers
    correlation_id = res.headers["X-Correlation-ID"]
    assert len(correlation_id) > 0


def test_metrics_registry_recording(client: TestClient):
    """
    Verifies that incoming API requests update the registry metrics
    and record response durations.
    """
    metrics_registry.reset()
    assert metrics_registry.total_requests == 0
    
    # Call endpoint to trigger metrics recording
    res = client.get("/api/v1/monitoring/health")
    assert res.status_code == 200
    
    # Verify incremented counter
    assert metrics_registry.total_requests == 1
    assert metrics_registry.get_average_response_time() > 0.0


def test_monitoring_api_endpoints(client: TestClient):
    """
    Checks that health, system, metrics, agents, tools, and plugins endpoints
    respond successfully.
    """
    # 1. GET /api/v1/monitoring/health
    res_h = client.get("/api/v1/monitoring/health")
    assert res_h.status_code == 200
    assert res_h.json()["success"] is True
    
    # 2. GET /api/v1/monitoring/system
    res_sys = client.get("/api/v1/monitoring/system")
    assert res_sys.status_code == 200
    assert res_sys.json()["success"] is True
    assert "cpu" in res_sys.json()["data"]
    assert "memory" in res_sys.json()["data"]
    
    # 3. GET /api/v1/monitoring/metrics
    res_m = client.get("/api/v1/monitoring/metrics")
    assert res_m.status_code == 200
    assert res_m.json()["success"] is True
    assert "total_requests" in res_m.json()["data"]
    
    # 4. GET /api/v1/monitoring/agents
    res_a = client.get("/api/v1/monitoring/agents")
    assert res_a.status_code == 200
    assert res_a.json()["success"] is True
    
    # 5. GET /api/v1/monitoring/tools
    res_t = client.get("/api/v1/monitoring/tools")
    assert res_t.status_code == 200
    assert res_t.json()["success"] is True
    
    # 6. GET /api/v1/monitoring/plugins
    res_p = client.get("/api/v1/monitoring/plugins")
    assert res_p.status_code == 200
    assert res_p.json()["success"] is True


def test_monitoring_cleanup_service(client: TestClient):
    """
    Verifies that the retention cleanup service endpoint executes successfully.
    """
    res_clean = client.post("/api/v1/monitoring/cleanup")
    assert res_clean.status_code == 200
    assert res_clean.json()["success"] is True
    assert "deleted_system_metrics" in res_clean.json()["data"]

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "description" in data
    assert "version" in data
    assert data["status"] == "running"
    assert "documentation_url" in data

def test_read_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["application"] == "healthy"
    assert data["database"] == "connected"
    assert data["redis"] == "connected"
    assert "version" in data
    assert "environment" in data
    assert "uptime" in data
    assert "timestamp" in data
    assert "python_version" in data
    assert data["api_version"] == "v1"

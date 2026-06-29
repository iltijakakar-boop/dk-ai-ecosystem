from fastapi.testclient import TestClient


def test_register_invalid_password(client: TestClient):
    # Password too short, missing digits and uppercase
    payload = {"email": "testuser@example.com", "password": "pwd"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_register_valid_password(client: TestClient):
    payload = {"email": "testuser@example.com", "password": "SecretPassword@123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "USER"


def test_login_success(client: TestClient):
    payload = {"username": "testuser@example.com", "password": "SecretPassword@123"}
    response = client.post("/api/v1/auth/login", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client: TestClient):
    payload = {"username": "testuser@example.com", "password": "WrongPassword@123"}
    response = client.post("/api/v1/auth/login", data=payload)
    assert response.status_code == 401


def test_protected_routes_unauthorized(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_protected_routes_authorized(client: TestClient):
    # Login to acquire token
    payload = {"username": "testuser@example.com", "password": "SecretPassword@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]

    # Query protected path
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "testuser@example.com"


def test_admin_only_forbidden_for_user(client: TestClient):
    # Login as standard USER
    payload = {"username": "testuser@example.com", "password": "SecretPassword@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]

    # Attempt to query admin route
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users/admin-only", headers=headers)
    assert response.status_code == 403


def test_admin_only_allowed_for_seeded_superuser(client: TestClient):
    # Login as seeded SUPER_ADMIN
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]

    # Query admin path
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users/admin-only", headers=headers)
    assert response.status_code == 200

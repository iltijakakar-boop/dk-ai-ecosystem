from fastapi.testclient import TestClient


def test_admin_dashboard_stats(client: TestClient):
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/admin/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "users_stats" in data["data"]
    assert data["data"]["users_stats"]["total"] >= 1


def test_user_pagination_and_search(client: TestClient):
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/api/v1/auth/register",
        json={"email": "alpha@example.com", "password": "SecretPassword@123"},
    )
    client.post(
        "/api/v1/auth/register",
        json={"email": "beta@example.com", "password": "SecretPassword@123"},
    )

    response = client.get("/api/v1/users?q=alpha", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "items" in res_data["data"]
    assert len(res_data["data"]["items"]) == 1
    assert res_data["data"]["items"][0]["email"] == "alpha@example.com"


def test_role_hierarchy_controls(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"email": "hierarchyuser@example.com", "password": "SecretPassword@123"},
    )
    payload_user = {
        "username": "hierarchyuser@example.com",
        "password": "SecretPassword@123",
    }
    user_login = client.post("/api/v1/auth/login", data=payload_user)
    user_token = user_login.json()["access_token"]
    headers_user = {"Authorization": f"Bearer {user_token}"}

    response = client.get("/api/v1/users", headers=headers_user)
    assert response.status_code == 403


def test_soft_delete(client: TestClient):
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "delete_me@example.com", "password": "SecretPassword@123"},
    )
    user_id = reg.json()["id"]

    del_response = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert del_response.status_code == 200

    get_res = client.get(f"/api/v1/users/{user_id}", headers=headers)
    assert get_res.status_code == 404


def test_audit_logs_created(client: TestClient):
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    login_response = client.post("/api/v1/auth/login", data=payload)
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "items" in res_data["data"]
    assert len(res_data["data"]["items"]) >= 1

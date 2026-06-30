from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.identity_service import identity_provider_service, session_service, passkey_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Identity Provider Registration
def test_identity_provider_config(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/identity/providers",
        json={"workspace_id": 1, "name": "okta-enterprise-sso"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "okta-enterprise-sso"


# 2. Session Revocation
def test_session_revocation(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        user_sess = session_service.create_session(session, workspace_id=1, user_id=1)
        session.commit()
        sess_id = user_sess.id
    finally:
        session.close()

    res = client.post(f"/api/v1/identity/sessions/{sess_id}/revoke", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["active"] is False


# 3. Passkeys Setup
def test_passkey_webauthn(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/identity/passkeys",
        json={
            "workspace_id": 1,
            "user_id": 1,
            "credential_id": "cred_xyz_12345",
            "public_key": "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE..."
        },
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["credential_id"] == "cred_xyz_12345"


# 4. Conditional Access Policy Engine
def test_conditional_access_policy(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/identity/policies",
        json={
            "workspace_id": 1,
            "name": "Zero Trust High Risk Policy",
            "mfa_required": True,
            "device_trust_required": True
        },
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["mfa_required"] is True

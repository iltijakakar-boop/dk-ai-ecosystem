from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import (
    OrganizationInvitation,
    Project,
    Workspace,
)
from app.services.billing_service import billing_service
from app.services.project_service import project_service
from app.services.usage_service import usage_service
from app.services.workspace_service import workspace_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_organization_and_workspace_lifecycle(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # 1. Create Organization
    org_payload = {"name": "Test Enterprise", "slug": "test-ent"}
    res = client.post("/api/v1/organizations", json=org_payload, headers=headers)
    assert res.status_code == 200
    org_data = res.json()["data"]
    org_id = org_data["id"]
    assert org_data["name"] == "Test Enterprise"
    assert org_data["slug"] == "test-ent"

    # 2. Get Organization details
    res = client.get(f"/api/v1/organizations/{org_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Test Enterprise"

    # 3. Create Workspace
    ws_payload = {
        "organization_id": org_id,
        "name": "Beta Workspace",
        "description": "Beta testing workspace.",
    }
    res = client.post("/api/v1/workspaces", json=ws_payload, headers=headers)
    assert res.status_code == 200
    ws_data = res.json()["data"]
    ws_id = ws_data["id"]
    assert ws_data["name"] == "Beta Workspace"

    # 4. Update Workspace settings & quotas
    settings_payload = {"settings": {"theme": "light", "language": "es"}}
    res = client.put(
        f"/api/v1/workspaces/{ws_id}/settings",
        json=settings_payload,
        headers=headers,
    )
    assert res.status_code == 200

    # 5. Verify settings updated
    res = client.get(f"/api/v1/workspaces/{ws_id}", headers=headers)
    assert res.status_code == 200
    assert "light" in res.json()["data"]["settings"]


def test_invitations_and_team_roles(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # Create Org
    res = client.post(
        "/api/v1/organizations",
        json={"name": "Invite Org", "slug": "invite-org"},
        headers=headers,
    )
    org_id = res.json()["data"]["id"]

    # 1. Send Invitation
    invite_payload = {"email": "invitee@example.com", "role": "Developer"}
    res = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json=invite_payload,
        headers=headers,
    )
    assert res.status_code == 200
    invite_data = res.json()["data"]
    token = invite_data["token"]
    assert invite_data["email"] == "invitee@example.com"
    assert invite_data["status"] == "Pending"

    # 2. Reject invitation
    res = client.post(
        "/api/v1/organizations/invitations/reject",
        json={"token": token},
        headers=headers,
    )
    assert res.status_code == 200

    # 3. Re-invite and Accept invitation (simulate accepting by admin user for test simplicity)
    res = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json=invite_payload,
        headers=headers,
    )
    token2 = res.json()["data"]["token"]
    res = client.post(
        "/api/v1/organizations/invitations/accept",
        json={"token": token2},
        headers=headers,
    )
    assert res.status_code == 200

    # 4. Verify Invitation Accepted in DB
    db_invite = (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.token == token2)
        .first()
    )
    assert db_invite.status == "Accepted"


def test_api_keys_and_service_accounts(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # Setup Workspace via API
    res_org = client.post(
        "/api/v1/organizations",
        json={"name": "Keys Org", "slug": "keys-org"},
        headers=headers,
    )
    org_id = res_org.json()["data"]["id"]

    res_ws = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Keys WS"},
        headers=headers,
    )
    ws_id = res_ws.json()["data"]["id"]

    # 1. Generate API Key
    key_payload = {
        "workspace_id": ws_id,
        "name": "Development Key",
        "permissions": ["agent.read", "workflow.read"],
    }
    res = client.post("/api/v1/api-keys", json=key_payload, headers=headers)
    assert res.status_code == 200
    key_data = res.json()["data"]
    api_key_str = key_data["api_key"]
    key_id = key_data["id"]
    assert api_key_str.startswith("dk_api_")

    # 2. Verify API Key works by using it to fetch statistics
    key_headers = {"Authorization": f"Bearer {api_key_str}"}
    res_verify = client.get(
        f"/api/v1/usage/statistics?workspace_id={ws_id}", headers=key_headers
    )
    assert res_verify.status_code == 200

    # 3. Rotate Key
    res = client.post(f"/api/v1/api-keys/{key_id}/rotate", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["api_key"].startswith("dk_api_")

    # 4. Service Account bot creation
    sa_payload = {
        "workspace_id": ws_id,
        "name": "Sync Bot",
        "permissions": ["agent.write"],
    }
    res = client.post("/api/v1/service-accounts", json=sa_payload, headers=headers)
    assert res.status_code == 200
    sa_data = res.json()["data"]
    sa_token = sa_data["token"]
    assert sa_token.startswith("dk_sa_")

    # 5. Verify Service Account Token works by using it to fetch statistics
    sa_headers = {"Authorization": f"Bearer {sa_token}"}
    res_verify_sa = client.get(
        f"/api/v1/usage/statistics?workspace_id={ws_id}", headers=sa_headers
    )
    assert res_verify_sa.status_code == 200


def test_encrypted_secrets_and_versioning(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    res_org = client.post(
        "/api/v1/organizations",
        json={"name": "Secrets Org", "slug": "sec-org"},
        headers=headers,
    )
    org_id = res_org.json()["data"]["id"]

    res_ws = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Secrets WS"},
        headers=headers,
    )
    ws_id = res_ws.json()["data"]["id"]

    # 1. Create Secret
    sec_payload = {
        "workspace_id": ws_id,
        "name": "DATABASE_URL",
        "value": "postgresql://db_user:password@localhost/db",
        "category": "database",
    }
    res = client.post("/api/v1/secrets", json=sec_payload, headers=headers)
    assert res.status_code == 200
    sec_id = res.json()["data"]["id"]
    assert res.json()["data"]["version"] == 1

    # 2. Decrypt Secret
    res = client.get(f"/api/v1/secrets/{sec_id}/decrypt", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["value"] == "postgresql://db_user:password@localhost/db"

    # 3. Update Secret value (increments version)
    update_payload = {"value": "postgresql://new_user:new_pass@localhost/db"}
    res = client.put(f"/api/v1/secrets/{sec_id}", json=update_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["version"] == 2

    # 4. Rollback to version 1
    res = client.post(f"/api/v1/secrets/{sec_id}/rollback?version=1", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["version"] == 3

    # Decrypt and verify value is rolled back
    res = client.get(f"/api/v1/secrets/{sec_id}/decrypt", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["value"] == "postgresql://db_user:password@localhost/db"


def test_usage_dashboard_search_and_export(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal

    headers = get_admin_headers(client)

    res_org = client.post(
        "/api/v1/organizations",
        json={"name": "Dashboard Org", "slug": "dash-org"},
        headers=headers,
    )
    org_id = res_org.json()["data"]["id"]

    res_ws = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Dashboard WS"},
        headers=headers,
    )
    ws_id = res_ws.json()["data"]["id"]

    # 1. Record Usage using an isolated connection session
    session = TestingSessionLocal()
    try:
        usage_service.record_usage(
            session,
            workspace_id=ws_id,
            tokens=5000,
            requests=10,
            response_latency_ms=120,
        )
        proj = Project(
            workspace_id=ws_id, name="Billing Analytics", description="Search target"
        )
        session.add(proj)
        session.commit()
    finally:
        session.close()

    # 2. Get Statistics
    res = client.get(f"/api/v1/usage/statistics?workspace_id={ws_id}", headers=headers)
    assert res.status_code == 200
    stats = res.json()["data"]
    assert stats["tokens"] == 5000
    assert stats["requests"] == 10

    # 3. Global Search
    res = client.get(
        f"/api/v1/usage/search?workspace_id={ws_id}&query=Billing",
        headers=headers,
    )
    assert res.status_code == 200
    search_results = res.json()["data"]
    assert len(search_results["projects"]) > 0

    # 4. Workspace Export
    res = client.get(f"/api/v1/usage/export?workspace_id={ws_id}", headers=headers)
    assert res.status_code == 200
    export_json = res.json()["data"]["export_json"]
    assert "Dashboard WS" in export_json


def test_quotas_and_billing_limits(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal

    headers = get_admin_headers(client)

    # 1. Create Organization (Starts on Free Plan by default)
    org_payload = {"name": "Limits Org", "slug": "limit-org"}
    res = client.post("/api/v1/organizations", json=org_payload, headers=headers)
    org_id = res.json()["data"]["id"]

    # Retrieve default workspace created during onboarding using isolated session
    session = TestingSessionLocal()
    try:
        ws = (
            session.query(Workspace).filter(Workspace.organization_id == org_id).first()
        )
        assert ws is not None
        ws_id = ws.id

        # Free Plan has limit for projects = 2 (defined in PLAN_QUOTAS)
        # Add 2 projects
        project_service.create_project(session, workspace_id=ws_id, name="Project A")
        project_service.create_project(session, workspace_id=ws_id, name="Project B")
        session.commit()

        # Asserting check_quota raises exception when adding 3rd project
        try:
            workspace_service.check_quota(
                session, workspace_id=ws_id, resource_type="projects"
            )
            assert False, "Should raise quota limit exception"
        except Exception as e:
            assert "Resource limit reached for projects" in str(e)

        # 2. Upgrade Organization plan to Business
        billing_service.update_organization_plan(
            session, org_id=org_id, plan_name="Business"
        )
        session.commit()

        # Quota is updated (Business allows 30 projects), check_quota should pass now
        workspace_service.check_quota(
            session, workspace_id=ws_id, resource_type="projects"
        )
    finally:
        session.close()

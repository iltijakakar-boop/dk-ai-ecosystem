from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.infrastructure_service import cluster_service, autoscaling_service, edge_ai_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Cluster Creation
def test_cluster_creation(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/infrastructure/clusters",
        json={"workspace_id": 1, "name": "k8s-prod-us-east", "api_endpoint": "https://10.0.0.1:6443"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "k8s-prod-us-east"


# 2. Deployments & Auto Scaling
def test_deployments_and_scaling(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    # Seed cluster and deployment first
    session = TestingSessionLocal()
    try:
        cluster = cluster_service.create_cluster(session, workspace_id=1, name="k8s-prod", api_endpoint="https://10.0.0.1")
        session.commit()
        dep = autoscaling_service.create_deployment(session, workspace_id=1, cluster_id=cluster.id, name="nginx-web", replicas=2)
        session.commit()
        dep_id = dep.id
    finally:
        session.close()

    # Scale the deployment to 4 replicas
    res = client.post(
        f"/api/v1/infrastructure/scale?deployment_id={dep_id}&replicas=4",
        headers=headers,
    )
    assert res.status_code == 200

    # Query active pods
    res_pods = client.get(f"/api/v1/infrastructure/pods?deployment_id={dep_id}", headers=headers)
    assert res_pods.status_code == 200
    assert len(res_pods.json()["data"]) == 4


# 3. Edge AI Device Registration
def test_edge_device_registration(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/infrastructure/edge/nodes",
        json={"workspace_id": 1, "name": "jetson-nano-edge-01"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "jetson-nano-edge-01"


# 4. Disaster Recovery Backups
def test_disaster_recovery_backups(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/infrastructure/backups/policy",
        json={"workspace_id": 1, "frequency": "daily"},
        headers=headers,
    )
    assert res.status_code == 200

    res_restore = client.post(
        "/api/v1/infrastructure/backups/restore?workspace_id=1",
        headers=headers,
    )
    assert res_restore.status_code == 200
    assert res_restore.json()["message"] == "Disaster recovery restore job triggered successfully."

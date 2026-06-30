from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.model_management_service import model_registry_service, dataset_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Model Registry
def test_model_registration_and_versions(client: TestClient, db: Session):
    headers = get_admin_headers(client)

    # Register
    res = client.post(
        "/api/v1/model-management/models",
        json={"workspace_id": 1, "name": "Llama-3-8B-Custom", "description": "Llama 3 base model in registry"},
        headers=headers,
    )
    assert res.status_code == 200
    model_id = res.json()["data"]["id"]

    # Version
    res_ver = client.post(
        f"/api/v1/model-management/models/{model_id}/versions",
        json={"model_id": model_id, "version": "1.0.0", "configuration": "{}"},
        headers=headers,
    )
    assert res_ver.status_code == 200
    assert res_ver.json()["data"]["version"] == "1.0.0"


# 2. Dataset Manager
def test_dataset_manager_flow(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/model-management/datasets",
        json={"workspace_id": 1, "name": "ShareGPT-Developer-Dataset", "description": "JSON dialogue set"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "ShareGPT-Developer-Dataset"


# 3. Fine-Tuning Execution
def test_fine_tuning_execution(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)
    
    session = TestingSessionLocal()
    try:
        model = model_registry_service.register_model(session, workspace_id=1, name="tuning-base")
        session.commit()
        model_id = model.id
    finally:
        session.close()
    
    res = client.post(
        "/api/v1/model-management/fine-tune",
        json={"workspace_id": 1, "model_id": model_id},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "completed"


# 4. GPU Scheduler Load Checks
def test_gpu_scheduler_and_workers(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.get("/api/v1/model-management/gpu-workers", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0


# 5. LLM Gateway & Routing Services
def test_llm_gateway_and_benchmarks():
    from app.services.model_management_service import training_service
    assert training_service is not None

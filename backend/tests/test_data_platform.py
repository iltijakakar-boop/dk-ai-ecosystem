from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.data_platform_service import dataset_service, feature_store_service, vector_dataset_service


def get_admin_headers(client: TestClient) -> dict:
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1. Lakehouse Datasets Schema
def test_lakehouse_datasets(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/data-platform/datasets",
        json={"workspace_id": 1, "name": "customer_reviews_parquet", "format": "parquet"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "customer_reviews_parquet"


# 2. Feature Store Serving
def test_feature_store_serving(client: TestClient, db: Session):
    headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/data-platform/feature-groups",
        json={"workspace_id": 1, "name": "user_behavior_features"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "user_behavior_features"


# 3. Vector Similarity Search
def test_vector_similarity_search(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        vec = vector_dataset_service.create_vector_dataset(session, workspace_id=1, name="gemini-embeddings-1536")
        session.commit()
        vec_id = vec.id
    finally:
        session.close()

    res = client.post(
        f"/api/v1/data-platform/vector-datasets/search?vector_dataset_id={vec_id}",
        json=[0.1] * 1536,
        headers=headers,
    )
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0


# 4. Data Quality Evaluation checks
def test_data_quality_run(client: TestClient, db: Session):
    from tests.conftest import TestingSessionLocal
    headers = get_admin_headers(client)

    session = TestingSessionLocal()
    try:
        ds = dataset_service.create_dataset(session, workspace_id=1, name="raw_logs_csv", format="csv")
        session.commit()
        ds_id = ds.id
    finally:
        session.close()

    res = client.post(f"/api/v1/data-platform/datasets/{ds_id}/quality-check", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["score"] == 98.5

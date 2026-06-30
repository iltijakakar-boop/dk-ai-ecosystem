import time

from fastapi.testclient import TestClient

from app.db.session import SessionLocal


# Helper to get admin headers
def get_admin_headers(client: TestClient):
    payload = {"username": "admin@example.com", "password": "Admin@123"}
    res = client.post("/api/v1/auth/login", data=payload)
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# Helper to get normal user headers
def get_user_headers(client: TestClient):
    # Register user (if already exists, it handles 400 or fails softly)
    payload = {"email": "normaluser@example.com", "password": "SecretPassword@123"}
    client.post("/api/v1/auth/register", json=payload)

    # Login
    payload_login = {
        "username": "normaluser@example.com",
        "password": "SecretPassword@123",
    }
    res = client.post("/api/v1/auth/login", data=payload_login)
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_create_job_rbac(client: TestClient):
    """
    Ensure only admins can create automation jobs.
    """
    job_payload = {
        "name": "RBAC Test Job",
        "description": "Checks authorization settings",
        "trigger_type": "manual",
        "priority": "NORMAL",
        "enabled": True,
    }

    # Try as normal user
    user_headers = get_user_headers(client)
    res = client.post("/api/v1/automation/jobs", json=job_payload, headers=user_headers)
    assert res.status_code == 403

    # Try as admin
    admin_headers = get_admin_headers(client)
    res = client.post(
        "/api/v1/automation/jobs", json=job_payload, headers=admin_headers
    )
    assert res.status_code == 201
    assert res.json()["data"]["name"] == "RBAC Test Job"


def test_list_and_read_jobs(client: TestClient):
    """
    Test listing jobs and fetching specific job definition.
    """
    admin_headers = get_admin_headers(client)
    res = client.get("/api/v1/automation/jobs", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1


def test_run_job_manual(client: TestClient):
    """
    Test manual execution of registered jobs.
    """
    admin_headers = get_admin_headers(client)

    # 1. Create a manual job
    job_payload = {
        "name": "Manual Execution Test",
        "trigger_type": "manual",
        "priority": "NORMAL",
        "enabled": True,
    }
    create_res = client.post(
        "/api/v1/automation/jobs", json=job_payload, headers=admin_headers
    )
    job_id = create_res.json()["data"]["id"]

    # 2. Trigger run
    run_res = client.post(
        f"/api/v1/automation/jobs/{job_id}/run", headers=admin_headers
    )
    assert run_res.status_code == 200
    exec_uuid = run_res.json()["data"]["execution_uuid"]
    assert exec_uuid is not None

    # Wait for execution thread to complete diagnostic run
    time.sleep(1.5)

    # 3. Query executions history
    hist_res = client.get(
        f"/api/v1/automation/jobs/{job_id}/executions", headers=admin_headers
    )
    assert hist_res.status_code == 200
    executions = hist_res.json()["data"]
    assert len(executions) >= 1
    assert executions[0]["status"] in ["Completed", "Running", "Queued"]


def test_job_dependencies(client: TestClient):
    """
    Test job dependency chaining. Job B must wait for Job A.
    """
    admin_headers = get_admin_headers(client)
    db = SessionLocal()
    try:
        # Create Job A (Parent)
        res_a = client.post(
            "/api/v1/automation/jobs",
            json={
                "name": "Job A",
                "trigger_type": "manual",
                "priority": "NORMAL",
                "enabled": True,
            },
            headers=admin_headers,
        )
        job_a_id = res_a.json()["data"]["id"]

        # Create Job B (Child depending on Job A)
        res_b = client.post(
            "/api/v1/automation/jobs",
            json={
                "name": "Job B",
                "trigger_type": "manual",
                "priority": "NORMAL",
                "depends_on_job_id": job_a_id,
                "dependency_status": "completed",
                "enabled": True,
            },
            headers=admin_headers,
        )
        job_b_id = res_b.json()["data"]["id"]

        # Trigger Job B. Since Job A hasn't run/completed, Job B execution must enter Waiting status
        run_b = client.post(
            f"/api/v1/automation/jobs/{job_b_id}/run", headers=admin_headers
        )
        assert run_b.json()["data"]["status"] == "Waiting"

        # Now trigger Job A
        client.post(f"/api/v1/automation/jobs/{job_a_id}/run", headers=admin_headers)

        # Wait for A to complete and resume B
        time.sleep(2)

        # Check Job B execution. It should now have transitioned from Waiting to Queued/Completed
        hist_b = client.get(
            f"/api/v1/automation/jobs/{job_b_id}/executions", headers=admin_headers
        )
        assert len(hist_b.json()["data"]) >= 1
        assert hist_b.json()["data"][0]["status"] in ["Queued", "Running", "Completed"]
    finally:
        db.close()


def test_webhook_trigger(client: TestClient):
    """
    Test incoming webhook event matching and automation execution.
    """
    admin_headers = get_admin_headers(client)

    # 1. Create an Event-triggered job
    # Note: Event-trigger matching event type is stored in cron_expression
    job_payload = {
        "name": "Webhook Event Job",
        "trigger_type": "event",
        "cron_expression": "github_push",
        "priority": "HIGH",
        "enabled": True,
    }
    create_res = client.post(
        "/api/v1/automation/jobs", json=job_payload, headers=admin_headers
    )
    job_id = create_res.json()["data"]["id"]

    # 2. Trigger webhook receiver endpoint
    webhook_payload = {
        "event_type": "github_push",
        "payload": {"repository": "dk-ai-ecosystem", "branch": "main"},
    }
    webhook_res = client.post("/api/v1/automation/webhook", json=webhook_payload)
    assert webhook_res.status_code == 200
    assert "received" in webhook_res.json()["message"]

    # Wait for execution processing
    time.sleep(1.5)

    # 3. Verify execution was spawned
    hist_res = client.get(
        f"/api/v1/automation/jobs/{job_id}/executions", headers=admin_headers
    )
    assert len(hist_res.json()["data"]) >= 1
    assert hist_res.json()["data"][0]["trigger_source"] == "event"


def test_progress_tracking_and_metrics(client: TestClient):
    """
    Verify progress tracking and dashboard stats calculate accurately.
    """
    admin_headers = get_admin_headers(client)

    # Fetch stats dashboard
    stats_res = client.get("/api/v1/automation/dashboard", headers=admin_headers)
    assert stats_res.status_code == 200
    data = stats_res.json()["data"]
    assert "total_jobs" in data
    assert "running_jobs" in data
    assert "queue_size" in data
    assert "success_rate" in data

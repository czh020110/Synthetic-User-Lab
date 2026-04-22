from fastapi.testclient import TestClient

from backend.main import app
from backend.stores.in_memory_run_store import run_store

client = TestClient(app)


def setup_function() -> None:
    run_store.clear()


def test_health_check() -> None:
    response = client.get("/api/v1/runs/demo/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_start_demo_run_returns_run_id() -> None:
    response = client.post(
        "/api/v1/runs/demo/start",
        json={
            "run_name": "demo",
            "expected_user_name": "Test User",
            "expected_email": "test@example.com",
            "headless": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert "run_id" in payload
    assert payload["status"] == "queued"

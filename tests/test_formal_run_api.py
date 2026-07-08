from __future__ import annotations

"""正式 Runs API 测试。"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.persona_schemas import Persona
from backend.schemas.task_schemas import Task
from backend.stores import get_entity_store, get_run_store


client = TestClient(app)


def setup_function():
    """每个测试前清空 store。"""
    get_entity_store().clear()
    get_run_store().clear()


def _create_persona_and_task():
    """创建一个 persona 和 task，返回它们的 id。"""
    entity_store = get_entity_store()
    persona = Persona(name="测试用户", skill_level="intermediate")
    entity_store.create_persona(persona)
    task = Task(name="测试任务", start_url="http://example.com", max_steps=5)
    entity_store.create_task(task)
    return persona.id, task.id


def test_start_formal_run_persona_not_found():
    _, task_id = _create_persona_and_task()
    # 删掉 persona 来测试 404
    get_entity_store().delete_persona(get_entity_store().list_personas()[0].id)
    resp = client.post("/api/v1/runs/start", json={
        "persona_id": "nonexistent",
        "task_id": task_id,
    })
    assert resp.status_code == 404
    assert "Persona" in resp.json()["detail"]


def test_start_formal_run_task_not_found():
    persona_id, _ = _create_persona_and_task()
    # 删掉 task 来测试 404
    get_entity_store().delete_task(get_entity_store().list_tasks()[0].id)
    resp = client.post("/api/v1/runs/start", json={
        "persona_id": persona_id,
        "task_id": "nonexistent",
    })
    assert resp.status_code == 404
    assert "Task" in resp.json()["detail"]


def test_start_formal_run_success():
    persona_id, task_id = _create_persona_and_task()
    with patch("backend.api.routes.runs.run_formal_workflow", new_callable=AsyncMock) as mock_workflow:
        resp = client.post("/api/v1/runs/start", json={
            "persona_id": persona_id,
            "task_id": task_id,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "run_id" in data
        assert data["status"] == "queued"


def test_start_formal_run_with_max_steps_override():
    persona_id, task_id = _create_persona_and_task()
    with patch("backend.api.routes.runs.run_formal_workflow", new_callable=AsyncMock):
        resp = client.post("/api/v1/runs/start", json={
            "persona_id": persona_id,
            "task_id": task_id,
            "max_steps_override": 3,
        })
    assert resp.status_code == 200
    run_id = resp.json()["data"]["run_id"]
    record = get_run_store().get_record(run_id)
    assert record is not None
    assert record.task.max_steps == 3
    task = get_entity_store().get_task(task_id)
    assert task is not None
    assert task.max_steps == 5


def test_get_run_status():
    persona_id, task_id = _create_persona_and_task()
    with patch("backend.api.routes.runs.run_formal_workflow", new_callable=AsyncMock):
        start_resp = client.post("/api/v1/runs/start", json={
            "persona_id": persona_id,
            "task_id": task_id,
        })
        run_id = start_resp.json()["data"]["run_id"]

    resp = client.get(f"/api/v1/runs/{run_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["run_id"] == run_id
    assert data["status"] in {"queued", "running"}


def test_get_run_status_not_found():
    resp = client.get("/api/v1/runs/nonexistent")
    assert resp.status_code == 404


def test_get_run_steps_not_found():
    resp = client.get("/api/v1/runs/nonexistent/steps")
    assert resp.status_code == 404


def test_get_run_report_not_found():
    resp = client.get("/api/v1/runs/nonexistent/report")
    assert resp.status_code == 404


def test_get_run_report_not_ready():
    persona_id, task_id = _create_persona_and_task()
    with patch("backend.api.routes.runs.run_formal_workflow", new_callable=AsyncMock):
        start_resp = client.post("/api/v1/runs/start", json={
            "persona_id": persona_id,
            "task_id": task_id,
        })
        run_id = start_resp.json()["data"]["run_id"]

    # run 还在执行中，报告未就绪
    resp = client.get(f"/api/v1/runs/{run_id}/report")
    assert resp.status_code == 409


def test_formal_run_request_validation():
    # 缺少 persona_id
    resp = client.post("/api/v1/runs/start", json={"task_id": "t1"})
    assert resp.status_code == 422
    # 缺少 task_id
    resp = client.post("/api/v1/runs/start", json={"persona_id": "p1"})
    assert resp.status_code == 422


def test_demo_run_still_works():
    """确认 demo run API 没有被正式 run 影响到。"""
    resp = client.post("/api/v1/runs/demo/start", json={"run_name": "test"})
    # demo run 可能因缺少浏览器环境而失败，但 API 层应返回 200 + queued
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "queued"

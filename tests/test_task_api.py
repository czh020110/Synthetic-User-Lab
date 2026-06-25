from __future__ import annotations

"""Task CRUD API 测试。"""

from fastapi.testclient import TestClient

from backend.main import app
from backend.stores import get_entity_store


client = TestClient(app)


def setup_function():
    """每个测试前清空 EntityStore。"""
    get_entity_store().clear()


def test_create_task():
    resp = client.post("/api/v1/tasks/", json={
        "name": "登录测试",
        "start_url": "http://example.com/login",
        "max_steps": 10,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "登录测试"
    assert data["start_url"] == "http://example.com/login"
    assert data["max_steps"] == 10
    assert "id" in data
    assert "created_at" in data


def test_create_task_with_defaults():
    resp = client.post("/api/v1/tasks/", json={
        "name": "默认任务",
        "start_url": "http://example.com",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["max_steps"] == 8
    assert data["risk_level"] == "low"
    assert data["destructive_action_allowed"] is False
    assert "navigate" in data["allowed_actions"]


def test_create_task_start_url_required():
    resp = client.post("/api/v1/tasks/", json={"name": "缺URL"})
    assert resp.status_code == 422


def test_create_task_max_steps_range():
    resp = client.post("/api/v1/tasks/", json={"name": "X", "start_url": "http://a.com", "max_steps": 0})
    assert resp.status_code == 422
    resp = client.post("/api/v1/tasks/", json={"name": "X", "start_url": "http://a.com", "max_steps": 51})
    assert resp.status_code == 422


def test_list_tasks():
    client.post("/api/v1/tasks/", json={"name": "T1", "start_url": "http://a.com"})
    client.post("/api/v1/tasks/", json={"name": "T2", "start_url": "http://b.com"})
    resp = client.get("/api/v1/tasks/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_get_task():
    create_resp = client.post("/api/v1/tasks/", json={"name": "查询任务", "start_url": "http://x.com"})
    task_id = create_resp.json()["data"]["id"]
    resp = client.get(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "查询任务"


def test_get_task_not_found():
    resp = client.get("/api/v1/tasks/nonexistent")
    assert resp.status_code == 404


def test_update_task():
    create_resp = client.post("/api/v1/tasks/", json={"name": "旧任务", "start_url": "http://old.com"})
    task_id = create_resp.json()["data"]["id"]
    resp = client.put(f"/api/v1/tasks/{task_id}", json={"name": "新任务", "max_steps": 20})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "新任务"
    assert data["max_steps"] == 20
    assert data["start_url"] == "http://old.com"


def test_update_task_not_found():
    resp = client.put("/api/v1/tasks/nonexistent", json={"name": "x"})
    assert resp.status_code == 404


def test_delete_task():
    create_resp = client.post("/api/v1/tasks/", json={"name": "待删除", "start_url": "http://d.com"})
    task_id = create_resp.json()["data"]["id"]
    resp = client.delete(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True
    assert client.get(f"/api/v1/tasks/{task_id}").status_code == 404


def test_delete_task_not_found():
    resp = client.delete("/api/v1/tasks/nonexistent")
    assert resp.status_code == 404

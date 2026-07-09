from __future__ import annotations

"""Persona CRUD API 测试。"""

from fastapi.testclient import TestClient

from backend.main import app
from backend.stores import get_entity_store


client = TestClient(app)


def setup_function():
    """每个测试前清空 EntityStore。"""
    get_entity_store().clear()


def test_create_persona():
    resp = client.post("/api/v1/personas/", json={"name": "新手用户", "skill_level": "newbie"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "新手用户"
    assert data["skill_level"] == "newbie"
    assert "id" in data
    assert "created_at" in data


def test_create_persona_with_defaults():
    resp = client.post("/api/v1/personas/", json={"name": "默认用户"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "默认用户"
    assert data["skill_level"] == "newbie"
    assert data["patience_level"] == "medium"
    assert data["risk_preference"] == "low"


def test_create_persona_name_required():
    resp = client.post("/api/v1/personas/", json={})
    assert resp.status_code == 422


def test_list_personas():
    client.post("/api/v1/personas/", json={"name": "A"})
    client.post("/api/v1/personas/", json={"name": "B"})
    resp = client.get("/api/v1/personas/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_get_persona():
    create_resp = client.post("/api/v1/personas/", json={"name": "查询用户"})
    persona_id = create_resp.json()["data"]["id"]
    resp = client.get(f"/api/v1/personas/{persona_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "查询用户"


def test_get_persona_not_found():
    resp = client.get("/api/v1/personas/nonexistent")
    assert resp.status_code == 404


def test_update_persona():
    create_resp = client.post("/api/v1/personas/", json={"name": "旧名"})
    persona_id = create_resp.json()["data"]["id"]
    resp = client.put(f"/api/v1/personas/{persona_id}", json={"name": "新名", "skill_level": "expert"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "新名"
    assert data["skill_level"] == "expert"


def test_update_persona_not_found():
    resp = client.put("/api/v1/personas/nonexistent", json={"name": "x"})
    assert resp.status_code == 404


def test_delete_persona():
    create_resp = client.post("/api/v1/personas/", json={"name": "待删除"})
    persona_id = create_resp.json()["data"]["id"]
    resp = client.delete(f"/api/v1/personas/{persona_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True
    # 确认已删除
    assert client.get(f"/api/v1/personas/{persona_id}").status_code == 404


def test_delete_persona_not_found():
    resp = client.delete("/api/v1/personas/nonexistent")
    assert resp.status_code == 404


def test_update_persona_clears_model_preset_id():
    """更新时显式传 model_preset_id=null 应清空（验证 exclude_unset 让可空字段可清空）。"""
    preset = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P", "provider": "openai", "model_name": "gpt-4o"},
    ).json()["data"]
    create_resp = client.post(
        "/api/v1/personas/",
        json={"name": "x", "model_preset_id": preset["id"]},
    )
    assert create_resp.json()["data"]["model_preset_id"] == preset["id"]
    persona_id = create_resp.json()["data"]["id"]

    # 显式传 null 清空（前端 ?? null 会发 null；后端 exclude_unset 保留显式 null）
    resp = client.put(f"/api/v1/personas/{persona_id}", json={"model_preset_id": None})
    assert resp.status_code == 200
    assert resp.json()["data"]["model_preset_id"] is None

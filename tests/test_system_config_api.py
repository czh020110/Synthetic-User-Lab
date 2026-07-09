from __future__ import annotations

"""系统配置 API 测试：模型预设 CRUD 与护栏关键词库读写。"""

from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.task_schemas import Task
from backend.stores import get_entity_store

client = TestClient(app)


def setup_function():
    get_entity_store().clear()


# ============================ 模型预设 ============================ #


def test_list_model_presets_empty():
    resp = client.get("/api/v1/system/model-presets")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_create_model_preset():
    resp = client.post(
        "/api/v1/system/model-presets",
        json={
            "name": "OpenAI GPT-4o",
            "provider": "openai",
            "api_key": "sk-test",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4o",
            "fast_model_name": "gpt-4o-mini",
            "is_default": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "OpenAI GPT-4o"
    assert data["provider"] == "openai"
    assert data["is_default"] is True
    assert "id" in data


def test_create_default_preset_clears_other_defaults():
    """新建默认预设时，其他预设的 is_default 应被互斥清空。"""
    r1 = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P1", "provider": "openai", "model_name": "gpt-4o", "is_default": True},
    )
    p1_id = r1.json()["data"]["id"]

    client.post(
        "/api/v1/system/model-presets",
        json={"name": "P2", "provider": "openai", "model_name": "gpt-4o-mini", "is_default": True},
    )

    presets = client.get("/api/v1/system/model-presets").json()["data"]
    p1 = next(p for p in presets if p["id"] == p1_id)
    assert p1["is_default"] is False
    p2 = next(p for p in presets if p["name"] == "P2")
    assert p2["is_default"] is True


def test_set_default_preset_mutual_exclusion():
    r1 = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P1", "provider": "openai", "model_name": "gpt-4o", "is_default": True},
    )
    p1_id = r1.json()["data"]["id"]
    r2 = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P2", "provider": "openai", "model_name": "gpt-4o-mini"},
    )
    p2_id = r2.json()["data"]["id"]

    resp = client.put(f"/api/v1/system/model-presets/{p2_id}/default")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_default"] is True

    presets = client.get("/api/v1/system/model-presets").json()["data"]
    assert next(p for p in presets if p["id"] == p1_id)["is_default"] is False
    assert next(p for p in presets if p["id"] == p2_id)["is_default"] is True


def test_set_default_preset_not_found():
    resp = client.put("/api/v1/system/model-presets/nonexistent/default")
    assert resp.status_code == 404


def test_update_model_preset():
    r = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P1", "provider": "openai", "model_name": "gpt-4o"},
    )
    pid = r.json()["data"]["id"]

    resp = client.put(f"/api/v1/system/model-presets/{pid}", json={"model_name": "gpt-4o-2024"})
    assert resp.status_code == 200
    assert resp.json()["data"]["model_name"] == "gpt-4o-2024"


def test_update_model_preset_not_found():
    resp = client.put("/api/v1/system/model-presets/nonexistent", json={"model_name": "x"})
    assert resp.status_code == 404


def test_delete_model_preset():
    r = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P1", "provider": "openai", "model_name": "gpt-4o"},
    )
    pid = r.json()["data"]["id"]
    resp = client.delete(f"/api/v1/system/model-presets/{pid}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True
    assert client.get("/api/v1/system/model-presets").json()["data"] == []


def test_delete_default_preset_forbidden():
    r = client.post(
        "/api/v1/system/model-presets",
        json={"name": "P1", "provider": "openai", "model_name": "gpt-4o", "is_default": True},
    )
    pid = r.json()["data"]["id"]
    resp = client.delete(f"/api/v1/system/model-presets/{pid}")
    assert resp.status_code == 400


def test_delete_model_preset_not_found():
    resp = client.delete("/api/v1/system/model-presets/nonexistent")
    assert resp.status_code == 404


# ============================ 护栏关键词库 ============================ #


def test_get_guard_config_returns_defaults():
    resp = client.get("/api/v1/system/guard-config")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "删除" in data["destructive_keywords"]
    assert r"\bpassword\b" in data["sensitive_keywords"]


def test_update_guard_config():
    resp = client.put(
        "/api/v1/system/guard-config",
        json={"destructive_keywords": ["删除", "buy"], "sensitive_keywords": ["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["destructive_keywords"] == ["删除", "buy"]
    assert data["sensitive_keywords"] == ["password"]

    # 持久化
    data2 = client.get("/api/v1/system/guard-config").json()["data"]
    assert data2["destructive_keywords"] == ["删除", "buy"]


def test_update_guard_config_partial():
    """只更新 destructive_keywords，sensitive_keywords 保持默认。"""
    client.put("/api/v1/system/guard-config", json={"destructive_keywords": ["buy"]})
    data = client.get("/api/v1/system/guard-config").json()["data"]
    assert data["destructive_keywords"] == ["buy"]
    assert r"\bpassword\b" in data["sensitive_keywords"]


def test_edited_guard_keywords_flow_to_action_guard():
    """编辑后的护栏关键词应真正影响 is_destructive_action 判定（验证 CRUD 与消费层接线）。"""
    from backend.execution.action_guard import is_destructive_action
    from backend.schemas.run_schemas import ActionInput, ClickActionPayload

    # 自定义关键词：只拦 "购买"
    client.put("/api/v1/system/guard-config", json={"destructive_keywords": ["购买"]})
    task = Task(start_url="https://example.com", destructive_action_allowed=False)

    blocked, _ = is_destructive_action(
        ActionInput(action="click", payload=ClickActionPayload(selector="button:has-text('立即购买')")),
        task,
    )
    assert blocked, "自定义关键词 '购买' 应被拦截"

    # 默认词库的 'Delete Account' 不再被拦（已被覆盖为只有 '购买'）
    not_blocked, _ = is_destructive_action(
        ActionInput(action="click", payload=ClickActionPayload(selector="button:has-text('Delete Account')")),
        task,
    )
    assert not not_blocked, "未配置的 delete 不应被拦截"


def test_empty_guard_keyword_is_dropped():
    """空字符串关键词应被 schema 剔除，避免 re.search('', text) 命中全部 selector。"""
    client.put(
        "/api/v1/system/guard-config",
        json={"destructive_keywords": ["购买", "", "  "]},
    )
    data = client.get("/api/v1/system/guard-config").json()["data"]
    assert data["destructive_keywords"] == ["购买"]

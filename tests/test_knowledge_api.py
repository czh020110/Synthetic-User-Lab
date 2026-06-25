from __future__ import annotations

"""KnowledgeItem CRUD API 测试。"""

from fastapi.testclient import TestClient

from backend.main import app
from backend.stores import get_entity_store


client = TestClient(app)


def setup_function():
    """每个测试前清空 EntityStore。"""
    get_entity_store().clear()


def test_create_knowledge_item():
    resp = client.post("/api/v1/knowledge/", json={
        "source_type": "product_knowledge",
        "title": "表单完成标准",
        "content": "表单需填写姓名和电话",
        "keywords": ["表单", "验证"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "表单完成标准"
    assert data["source_type"] == "product_knowledge"
    assert "id" in data
    assert "created_at" in data


def test_create_knowledge_item_required_fields():
    resp = client.post("/api/v1/knowledge/", json={"source_type": "failure_case"})
    assert resp.status_code == 422  # title and content required


def test_list_knowledge_items():
    client.post("/api/v1/knowledge/", json={"source_type": "product_knowledge", "title": "P1", "content": "c1"})
    client.post("/api/v1/knowledge/", json={"source_type": "failure_case", "title": "F1", "content": "c2"})
    resp = client.get("/api/v1/knowledge/")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_list_knowledge_items_filter_by_source_type():
    client.post("/api/v1/knowledge/", json={"source_type": "product_knowledge", "title": "P1", "content": "c1"})
    client.post("/api/v1/knowledge/", json={"source_type": "failure_case", "title": "F1", "content": "c2"})
    resp = client.get("/api/v1/knowledge/?source_type=product_knowledge")
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["source_type"] == "product_knowledge"


def test_get_knowledge_item():
    create_resp = client.post("/api/v1/knowledge/", json={
        "source_type": "product_knowledge", "title": "查询条目", "content": "内容",
    })
    item_id = create_resp.json()["data"]["id"]
    resp = client.get(f"/api/v1/knowledge/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "查询条目"


def test_get_knowledge_item_not_found():
    resp = client.get("/api/v1/knowledge/nonexistent")
    assert resp.status_code == 404


def test_update_knowledge_item():
    create_resp = client.post("/api/v1/knowledge/", json={
        "source_type": "failure_case", "title": "旧标题", "content": "旧内容",
    })
    item_id = create_resp.json()["data"]["id"]
    resp = client.put(f"/api/v1/knowledge/{item_id}", json={"title": "新标题", "keywords": ["新关键词"]})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "新标题"
    assert data["content"] == "旧内容"
    assert data["keywords"] == ["新关键词"]


def test_update_knowledge_item_not_found():
    resp = client.put("/api/v1/knowledge/nonexistent", json={"title": "x"})
    assert resp.status_code == 404


def test_delete_knowledge_item():
    create_resp = client.post("/api/v1/knowledge/", json={
        "source_type": "product_knowledge", "title": "待删除", "content": "c",
    })
    item_id = create_resp.json()["data"]["id"]
    resp = client.delete(f"/api/v1/knowledge/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["deleted"] is True
    assert client.get(f"/api/v1/knowledge/{item_id}").status_code == 404


def test_delete_knowledge_item_not_found():
    resp = client.delete("/api/v1/knowledge/nonexistent")
    assert resp.status_code == 404

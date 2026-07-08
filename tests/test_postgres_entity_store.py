from __future__ import annotations

import os

import pytest

from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemUpdate
from backend.schemas.persona_schemas import Persona, PersonaUpdate
from backend.schemas.settings_schemas import FrontendSettings
from backend.schemas.task_schemas import Task, TaskUpdate
from backend.stores.postgres_entity_store import PostgresEntityStore

POSTGRES_TEST_DSN_ENV = "SYNTHETIC_USER_LAB_POSTGRES_TEST_DSN"


def _postgres_test_dsn() -> str:
    dsn = os.getenv(POSTGRES_TEST_DSN_ENV)
    if not dsn:
        pytest.skip(f"{POSTGRES_TEST_DSN_ENV} is not configured")
    return dsn


@pytest.fixture
def store() -> PostgresEntityStore:
    store = PostgresEntityStore(_postgres_test_dsn())
    store.initialize()
    store.clear()
    yield store
    store.clear()
    store.close()


class TestPostgresEntityStorePersona:
    def test_create_and_get(self, store: PostgresEntityStore) -> None:
        persona = Persona(name="Postgres用户")
        store.create_persona(persona)
        got = store.get_persona(persona.id)
        assert got is not None
        assert got.name == "Postgres用户"

    def test_persistence_across_reopen(self, store: PostgresEntityStore) -> None:
        persona = Persona(name="持久化用户")
        store.create_persona(persona)
        store.close()

        store2 = PostgresEntityStore(_postgres_test_dsn())
        store2.initialize()
        got = store2.get_persona(persona.id)
        assert got is not None
        assert got.name == "持久化用户"
        store2.clear()
        store2.close()

    def test_list_update_delete(self, store: PostgresEntityStore) -> None:
        p1 = Persona(name="A")
        p2 = Persona(name="B")
        store.create_persona(p1)
        store.create_persona(p2)
        assert len(store.list_personas()) == 2

        updated = store.update_persona(p1.id, PersonaUpdate(name="A2"))
        assert updated is not None
        assert updated.name == "A2"
        assert store.delete_persona(p2.id) is True
        assert len(store.list_personas()) == 1


class TestPostgresEntityStoreTask:
    def test_create_and_get(self, store: PostgresEntityStore) -> None:
        task = Task(name="Postgres任务", start_url="http://postgres.com")
        store.create_task(task)
        got = store.get_task(task.id)
        assert got is not None
        assert got.name == "Postgres任务"

    def test_persistence_across_reopen(self, store: PostgresEntityStore) -> None:
        task = Task(name="持久化任务", start_url="http://persist.com")
        store.create_task(task)
        store.close()

        store2 = PostgresEntityStore(_postgres_test_dsn())
        store2.initialize()
        got = store2.get_task(task.id)
        assert got is not None
        assert got.name == "持久化任务"
        store2.clear()
        store2.close()

    def test_update_and_delete(self, store: PostgresEntityStore) -> None:
        task = Task(name="旧任务", start_url="http://old.com")
        store.create_task(task)
        updated = store.update_task(task.id, TaskUpdate(name="新任务"))
        assert updated is not None
        assert updated.name == "新任务"
        assert store.delete_task(task.id) is True
        assert store.get_task(task.id) is None


class TestPostgresEntityStoreKnowledge:
    def test_create_and_get(self, store: PostgresEntityStore) -> None:
        item = KnowledgeItem(source_type="product_knowledge", title="Postgres知识", content="测试内容")
        store.create_knowledge_item(item)
        got = store.get_knowledge_item(item.id)
        assert got is not None
        assert got.title == "Postgres知识"

    def test_list_with_filter(self, store: PostgresEntityStore) -> None:
        store.create_knowledge_item(KnowledgeItem(source_type="product_knowledge", title="P", content="c"))
        store.create_knowledge_item(KnowledgeItem(source_type="failure_case", title="F", content="c"))
        pk = store.list_knowledge_items(source_type="product_knowledge")
        assert len(pk) == 1
        assert pk[0].source_type == "product_knowledge"

    def test_update_and_delete(self, store: PostgresEntityStore) -> None:
        item = KnowledgeItem(source_type="failure_case", title="旧标题", content="c")
        store.create_knowledge_item(item)
        updated = store.update_knowledge_item(item.id, KnowledgeItemUpdate(title="新标题"))
        assert updated is not None
        assert updated.title == "新标题"
        assert store.delete_knowledge_item(item.id) is True
        assert store.get_knowledge_item(item.id) is None


class TestPostgresEntityStoreFrontendSettings:
    def test_get_defaults(self, store: PostgresEntityStore) -> None:
        settings = store.get_frontend_settings()
        assert settings.theme == "light"
        assert settings.locale == "zh-CN"

    def test_persistence_across_reopen(self, store: PostgresEntityStore) -> None:
        settings = store.get_frontend_settings().model_copy(update={"theme": "dark", "default_max_steps": 26})
        store.upsert_frontend_settings(settings)
        store.close()

        store2 = PostgresEntityStore(_postgres_test_dsn())
        store2.initialize()
        got = store2.get_frontend_settings()
        assert got.theme == "dark"
        assert got.default_max_steps == 26
        store2.clear()
        store2.close()


def test_get_pool_closes_half_initialized_pool_on_wait_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    created_pool = None

    class FakePool:
        def __init__(self, **_kwargs) -> None:
            self.closed = False

        def wait(self) -> None:
            raise RuntimeError("boom")

        def close(self) -> None:
            self.closed = True

    def fake_connection_pool(**kwargs):
        nonlocal created_pool
        created_pool = FakePool(**kwargs)
        return created_pool

    monkeypatch.setattr("backend.stores.postgres_entity_store.ConnectionPool", fake_connection_pool)
    store = PostgresEntityStore("postgresql://test:test@localhost:5432/test")

    with pytest.raises(RuntimeError, match="boom"):
        store._get_pool()

    assert created_pool is not None
    assert created_pool.closed is True
    assert store._pool is None

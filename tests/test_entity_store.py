from __future__ import annotations

"""EntityStore 协议实现的单元测试，覆盖 InMemoryEntityStore 和 SqliteEntityStore。"""

import tempfile
from pathlib import Path

import pytest

from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemCreate, KnowledgeItemUpdate
from backend.schemas.persona_schemas import Persona, PersonaCreate, PersonaUpdate
from backend.schemas.settings_schemas import FrontendSettings
from backend.schemas.task_schemas import Task, TaskCreate, TaskUpdate


# ============================ InMemoryEntityStore ============================ #


class TestInMemoryEntityStorePersona:
    def setup_method(self):
        from backend.stores.in_memory_entity_store import InMemoryEntityStore

        self.store = InMemoryEntityStore()

    def test_create_and_get_persona(self):
        persona = Persona(name="新手用户", skill_level="newbie")
        created = self.store.create_persona(persona)
        assert created.id == persona.id
        assert created.name == "新手用户"

        got = self.store.get_persona(persona.id)
        assert got is not None
        assert got.name == "新手用户"

    def test_get_persona_not_found(self):
        assert self.store.get_persona("nonexistent") is None

    def test_list_personas(self):
        self.store.create_persona(Persona(name="A"))
        self.store.create_persona(Persona(name="B"))
        result = self.store.list_personas()
        assert len(result) == 2

    def test_update_persona(self):
        persona = Persona(name="旧名")
        self.store.create_persona(persona)
        updated = self.store.update_persona(persona.id, PersonaUpdate(name="新名"))
        assert updated is not None
        assert updated.name == "新名"

    def test_update_persona_not_found(self):
        assert self.store.update_persona("nonexistent", PersonaUpdate(name="x")) is None

    def test_delete_persona(self):
        persona = Persona(name="待删除")
        self.store.create_persona(persona)
        assert self.store.delete_persona(persona.id) is True
        assert self.store.get_persona(persona.id) is None

    def test_delete_persona_not_found(self):
        assert self.store.delete_persona("nonexistent") is False

    def test_clear(self):
        self.store.create_persona(Persona(name="A"))
        self.store.create_task(Task(name="T", start_url="http://example.com"))
        self.store.clear()
        assert self.store.list_personas() == []
        assert self.store.list_tasks() == []


class TestInMemoryEntityStoreTask:
    def setup_method(self):
        from backend.stores.in_memory_entity_store import InMemoryEntityStore

        self.store = InMemoryEntityStore()

    def test_create_and_get_task(self):
        task = Task(name="登录测试", start_url="http://example.com/login")
        created = self.store.create_task(task)
        assert created.id == task.id
        assert created.start_url == "http://example.com/login"

        got = self.store.get_task(task.id)
        assert got is not None
        assert got.name == "登录测试"

    def test_get_task_not_found(self):
        assert self.store.get_task("nonexistent") is None

    def test_list_tasks(self):
        self.store.create_task(Task(name="T1", start_url="http://a.com"))
        self.store.create_task(Task(name="T2", start_url="http://b.com"))
        assert len(self.store.list_tasks()) == 2

    def test_update_task(self):
        task = Task(name="旧任务", start_url="http://old.com")
        self.store.create_task(task)
        updated = self.store.update_task(task.id, TaskUpdate(name="新任务", start_url="http://new.com"))
        assert updated is not None
        assert updated.name == "新任务"
        assert updated.start_url == "http://new.com"

    def test_delete_task(self):
        task = Task(name="待删除", start_url="http://x.com")
        self.store.create_task(task)
        assert self.store.delete_task(task.id) is True
        assert self.store.get_task(task.id) is None


class TestInMemoryEntityStoreKnowledge:
    def setup_method(self):
        from backend.stores.in_memory_entity_store import InMemoryEntityStore

        self.store = InMemoryEntityStore()

    def test_create_and_get_knowledge_item(self):
        item = KnowledgeItem(source_type="product_knowledge", title="表单标准", content="表单需填写姓名和电话")
        created = self.store.create_knowledge_item(item)
        assert created.id == item.id

        got = self.store.get_knowledge_item(item.id)
        assert got is not None
        assert got.title == "表单标准"

    def test_list_knowledge_items_with_filter(self):
        self.store.create_knowledge_item(KnowledgeItem(source_type="product_knowledge", title="P1", content="c1"))
        self.store.create_knowledge_item(KnowledgeItem(source_type="failure_case", title="F1", content="c2"))
        pk_items = self.store.list_knowledge_items(source_type="product_knowledge")
        assert len(pk_items) == 1
        assert pk_items[0].source_type == "product_knowledge"

    def test_update_knowledge_item(self):
        item = KnowledgeItem(source_type="product_knowledge", title="旧标题", content="旧内容")
        self.store.create_knowledge_item(item)
        updated = self.store.update_knowledge_item(item.id, KnowledgeItemUpdate(title="新标题"))
        assert updated is not None
        assert updated.title == "新标题"
        assert updated.content == "旧内容"

    def test_delete_knowledge_item(self):
        item = KnowledgeItem(source_type="failure_case", title="待删", content="c")
        self.store.create_knowledge_item(item)
        assert self.store.delete_knowledge_item(item.id) is True
        assert self.store.get_knowledge_item(item.id) is None


class TestInMemoryEntityStoreFrontendSettings:
    def setup_method(self):
        from backend.stores.in_memory_entity_store import InMemoryEntityStore

        self.store = InMemoryEntityStore()

    def test_get_defaults(self):
        settings = self.store.get_frontend_settings()
        assert settings.theme == "light"
        assert settings.locale == "zh-CN"
        assert settings.default_max_steps == 30

    def test_upsert_settings(self):
        settings = self.store.get_frontend_settings()
        updated = settings.model_copy(update={"theme": "dark", "default_max_steps": 18})
        saved = self.store.upsert_frontend_settings(updated)
        assert saved.theme == "dark"
        assert saved.default_max_steps == 18
        assert self.store.get_frontend_settings().theme == "dark"


# ============================ SqliteEntityStore ============================ #


@pytest.fixture
def sqlite_store():
    from backend.stores.sqlite_entity_store import SqliteEntityStore

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    store = SqliteEntityStore(db_path)
    store.initialize()
    yield store
    store.close()
    Path(db_path).unlink(missing_ok=True)


class TestSqliteEntityStorePersona:
    def test_create_and_get(self, sqlite_store):
        persona = Persona(name="SQLite用户")
        sqlite_store.create_persona(persona)
        got = sqlite_store.get_persona(persona.id)
        assert got is not None
        assert got.name == "SQLite用户"

    def test_persistence_across_reopen(self, sqlite_store):
        from backend.stores.sqlite_entity_store import SqliteEntityStore

        persona = Persona(name="持久化用户")
        sqlite_store.create_persona(persona)
        db_path = sqlite_store._db_path

        sqlite_store.close()
        store2 = SqliteEntityStore(db_path)
        store2.initialize()
        got = store2.get_persona(persona.id)
        assert got is not None
        assert got.name == "持久化用户"
        store2.close()

    def test_list_and_delete(self, sqlite_store):
        p1 = Persona(name="A")
        p2 = Persona(name="B")
        sqlite_store.create_persona(p1)
        sqlite_store.create_persona(p2)
        assert len(sqlite_store.list_personas()) == 2
        sqlite_store.delete_persona(p1.id)
        assert len(sqlite_store.list_personas()) == 1

    def test_update(self, sqlite_store):
        persona = Persona(name="旧名")
        sqlite_store.create_persona(persona)
        updated = sqlite_store.update_persona(persona.id, PersonaUpdate(name="新名"))
        assert updated is not None
        assert updated.name == "新名"


class TestSqliteEntityStoreTask:
    def test_create_and_get(self, sqlite_store):
        task = Task(name="SQLite任务", start_url="http://sqlite.com")
        sqlite_store.create_task(task)
        got = sqlite_store.get_task(task.id)
        assert got is not None
        assert got.name == "SQLite任务"

    def test_persistence_across_reopen(self, sqlite_store):
        from backend.stores.sqlite_entity_store import SqliteEntityStore

        task = Task(name="持久化任务", start_url="http://persist.com")
        sqlite_store.create_task(task)
        db_path = sqlite_store._db_path

        sqlite_store.close()
        store2 = SqliteEntityStore(db_path)
        store2.initialize()
        got = store2.get_task(task.id)
        assert got is not None
        assert got.name == "持久化任务"
        store2.close()

    def test_update(self, sqlite_store):
        task = Task(name="旧任务", start_url="http://old.com")
        sqlite_store.create_task(task)
        updated = sqlite_store.update_task(task.id, TaskUpdate(name="新任务"))
        assert updated is not None
        assert updated.name == "新任务"


class TestSqliteEntityStoreKnowledge:
    def test_create_and_get(self, sqlite_store):
        item = KnowledgeItem(source_type="product_knowledge", title="SQLite知识", content="测试内容")
        sqlite_store.create_knowledge_item(item)
        got = sqlite_store.get_knowledge_item(item.id)
        assert got is not None
        assert got.title == "SQLite知识"

    def test_list_with_filter(self, sqlite_store):
        sqlite_store.create_knowledge_item(KnowledgeItem(source_type="product_knowledge", title="P", content="c"))
        sqlite_store.create_knowledge_item(KnowledgeItem(source_type="failure_case", title="F", content="c"))
        pk = sqlite_store.list_knowledge_items(source_type="product_knowledge")
        assert len(pk) == 1

    def test_update_and_delete(self, sqlite_store):
        item = KnowledgeItem(source_type="failure_case", title="旧标题", content="c")
        sqlite_store.create_knowledge_item(item)
        updated = sqlite_store.update_knowledge_item(item.id, KnowledgeItemUpdate(title="新标题"))
        assert updated is not None
        assert updated.title == "新标题"
        assert sqlite_store.delete_knowledge_item(item.id) is True
        assert sqlite_store.get_knowledge_item(item.id) is None


class TestSqliteEntityStoreFrontendSettings:
    def test_get_defaults(self, sqlite_store):
        settings = sqlite_store.get_frontend_settings()
        assert settings.theme == "light"
        assert settings.locale == "zh-CN"

    def test_upsert_and_reopen(self, sqlite_store):
        from backend.stores.sqlite_entity_store import SqliteEntityStore

        settings = sqlite_store.get_frontend_settings().model_copy(update={"theme": "dark", "default_max_steps": 22})
        sqlite_store.upsert_frontend_settings(settings)
        db_path = sqlite_store._db_path

        sqlite_store.close()
        store2 = SqliteEntityStore(db_path)
        store2.initialize()
        got = store2.get_frontend_settings()
        assert got.theme == "dark"
        assert got.default_max_steps == 22
        store2.close()

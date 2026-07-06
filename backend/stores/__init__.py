from __future__ import annotations

# ============================ 存储层入口模块 ============================ #
# 模块功能: 提供 get_run_store() 和 get_entity_store() 工厂函数
# 模块接口说明: get_run_store() 返回 RunStore 实例，get_entity_store() 返回 EntityStore 实例

from backend.core.config import resolve_database_backend
from backend.stores.entity_store_protocol import EntityStore
from backend.stores.run_store_protocol import RunStore

__all__ = ["RunStore", "get_run_store", "_reset_run_store", "get_entity_store", "_reset_entity_store"]

_run_store: RunStore | None = None
_entity_store: EntityStore | None = None


def _create_run_store(database_url: str) -> RunStore:
    backend = resolve_database_backend(database_url)
    if backend == "memory":
        from backend.stores.in_memory_run_store import InMemoryRunStore

        return InMemoryRunStore()
    if backend == "postgres":
        from backend.stores.postgres_run_store import PostgresRunStore

        store = PostgresRunStore(database_url)
        store.initialize()
        return store
    from backend.stores.sqlite_run_store import SqliteRunStore

    store = SqliteRunStore(database_url)
    store.initialize()
    return store


def _create_entity_store(database_url: str) -> EntityStore:
    backend = resolve_database_backend(database_url)
    if backend == "memory":
        from backend.stores.in_memory_entity_store import InMemoryEntityStore

        return InMemoryEntityStore()
    if backend == "postgres":
        from backend.stores.postgres_entity_store import PostgresEntityStore

        store = PostgresEntityStore(database_url)
        store.initialize()
        return store
    from backend.stores.sqlite_entity_store import SqliteEntityStore

    store = SqliteEntityStore(database_url)
    store.initialize()
    return store


def get_run_store() -> RunStore:
    """按配置返回全局 run_store 实例。"""

    global _run_store
    if _run_store is None:
        from backend.core.config import get_settings

        _run_store = _create_run_store(get_settings().database_url)
    return _run_store


def _reset_run_store() -> None:
    """仅用于测试和关闭：关闭连接并重置全局单例。"""

    global _run_store
    if _run_store is not None and hasattr(_run_store, "close"):
        _run_store.close()
    _run_store = None


def get_entity_store() -> EntityStore:
    """按配置返回全局 entity_store 实例。"""

    global _entity_store
    if _entity_store is None:
        from backend.core.config import get_settings

        _entity_store = _create_entity_store(get_settings().database_url)
    return _entity_store


def _reset_entity_store() -> None:
    """仅用于测试和关闭：关闭连接并重置全局单例。"""

    global _entity_store
    if _entity_store is not None and hasattr(_entity_store, "close"):
        _entity_store.close()
    _entity_store = None

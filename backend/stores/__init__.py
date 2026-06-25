from __future__ import annotations

# ============================ 存储层入口模块 ============================ #
# 模块功能: 提供 get_run_store() 和 get_entity_store() 工厂函数
# 模块接口说明: get_run_store() 返回 RunStore 实例，get_entity_store() 返回 EntityStore 实例

from backend.stores.entity_store_protocol import EntityStore
from backend.stores.run_store_protocol import RunStore

__all__ = ["RunStore", "get_run_store", "_reset_run_store", "get_entity_store", "_reset_entity_store"]

_run_store: RunStore | None = None
_entity_store: EntityStore | None = None


def get_run_store() -> RunStore:
    """按配置返回全局 run_store 实例。

    - 如果 SYNTHETIC_USER_LAB_DATABASE_URL 为 ":memory:"，返回 InMemoryRunStore
    - 否则返回 SqliteRunStore 并初始化数据库
    """

    global _run_store
    if _run_store is None:
        from backend.core.config import get_settings

        settings = get_settings()
        db_path = str(settings.database_url)
        if db_path == ":memory:":
            from backend.stores.in_memory_run_store import InMemoryRunStore

            _run_store = InMemoryRunStore()
        else:
            from backend.stores.sqlite_run_store import SqliteRunStore

            store = SqliteRunStore(db_path)
            store.initialize()
            _run_store = store
    return _run_store


def _reset_run_store() -> None:
    """仅用于测试和关闭：关闭连接并重置全局单例。"""

    global _run_store
    if _run_store is not None and hasattr(_run_store, "close"):
        _run_store.close()
    _run_store = None


def get_entity_store() -> EntityStore:
    """按配置返回全局 entity_store 实例。

    - 如果 SYNTHETIC_USER_LAB_DATABASE_URL 为 ":memory:"，返回 InMemoryEntityStore
    - 否则返回 SqliteEntityStore 并初始化数据库
    """

    global _entity_store
    if _entity_store is None:
        from backend.core.config import get_settings

        settings = get_settings()
        db_path = str(settings.database_url)
        if db_path == ":memory:":
            from backend.stores.in_memory_entity_store import InMemoryEntityStore

            _entity_store = InMemoryEntityStore()
        else:
            from backend.stores.sqlite_entity_store import SqliteEntityStore

            store = SqliteEntityStore(db_path)
            store.initialize()
            _entity_store = store
    return _entity_store


def _reset_entity_store() -> None:
    """仅用于测试和关闭：关闭连接并重置全局单例。"""

    global _entity_store
    if _entity_store is not None and hasattr(_entity_store, "close"):
        _entity_store.close()
    _entity_store = None

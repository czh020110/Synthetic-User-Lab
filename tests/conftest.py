from __future__ import annotations

# ============================ 测试配置 ============================ #
# 确保 tests/ 下所有测试使用 InMemoryRunStore 和 InMemoryEntityStore，不依赖文件数据库。

import backend.stores as stores_mod
from backend.stores.in_memory_entity_store import InMemoryEntityStore
from backend.stores.in_memory_run_store import InMemoryRunStore


def pytest_configure(config) -> None:
    """在测试开始前将 store 单例替换为内存实现。"""

    stores_mod._run_store = InMemoryRunStore()
    stores_mod._entity_store = InMemoryEntityStore()

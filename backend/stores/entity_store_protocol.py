from __future__ import annotations

# ============================ EntityStore 协议定义 ============================ #
# 模块功能: 定义实体存储层的统一接口，InMemoryEntityStore 与 SqliteEntityStore 均实现此协议
# 模块接口说明: EntityStore Protocol 提供 Persona/Task/KnowledgeItem 的 CRUD 方法签名

from typing import Protocol, runtime_checkable

from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemUpdate
from backend.schemas.persona_schemas import Persona, PersonaUpdate
from backend.schemas.settings_schemas import FrontendSettings
from backend.schemas.task_schemas import Task, TaskUpdate


@runtime_checkable
class EntityStore(Protocol):
    """实体存储层统一接口。

    InMemoryEntityStore 和 SqliteEntityStore 均实现此协议。
    """

    # ============================ Persona CRUD ============================ #

    def create_persona(self, persona: Persona) -> Persona:
        """创建新的 persona 记录。"""
        ...

    def get_persona(self, persona_id: str) -> Persona | None:
        """返回指定 persona。"""
        ...

    def list_personas(self) -> list[Persona]:
        """返回所有 persona 列表。"""
        ...

    def update_persona(self, persona_id: str, updates: PersonaUpdate) -> Persona | None:
        """更新指定 persona，返回更新后的对象或 None（不存在时）。"""
        ...

    def delete_persona(self, persona_id: str) -> bool:
        """删除指定 persona，返回是否成功删除。"""
        ...

    # ============================ Task CRUD ============================ #

    def create_task(self, task: Task) -> Task:
        """创建新的 task 记录。"""
        ...

    def get_task(self, task_id: str) -> Task | None:
        """返回指定 task。"""
        ...

    def list_tasks(self) -> list[Task]:
        """返回所有 task 列表。"""
        ...

    def update_task(self, task_id: str, updates: TaskUpdate) -> Task | None:
        """更新指定 task，返回更新后的对象或 None（不存在时）。"""
        ...

    def delete_task(self, task_id: str) -> bool:
        """删除指定 task，返回是否成功删除。"""
        ...

    # ============================ KnowledgeItem CRUD ============================ #

    def create_knowledge_item(self, item: KnowledgeItem) -> KnowledgeItem:
        """创建新的知识条目。"""
        ...

    def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        """返回指定知识条目。"""
        ...

    def list_knowledge_items(self, source_type: str | None = None) -> list[KnowledgeItem]:
        """返回知识条目列表，可按 source_type 过滤。"""
        ...

    def update_knowledge_item(self, item_id: str, updates: KnowledgeItemUpdate) -> KnowledgeItem | None:
        """更新指定知识条目，返回更新后的对象或 None（不存在时）。"""
        ...

    def delete_knowledge_item(self, item_id: str) -> bool:
        """删除指定知识条目，返回是否成功删除。"""
        ...

    # ============================ FrontendSettings ============================ #

    def get_frontend_settings(self) -> FrontendSettings:
        """返回前端设置；若未显式保存则返回默认值。"""
        ...

    def upsert_frontend_settings(self, settings: FrontendSettings) -> FrontendSettings:
        """写入并返回当前前端设置。"""
        ...

    # ============================ 通用 ============================ #

    def clear(self) -> None:
        """清空全部数据。仅用于测试。"""
        ...

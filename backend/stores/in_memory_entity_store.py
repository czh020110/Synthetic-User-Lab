from __future__ import annotations

# ============================ 内存实体存储模块 ============================ #
# 模块功能: 使用内存字典存储 Persona/Task/KnowledgeItem，供开发和测试使用
# 模块接口说明: InMemoryEntityStore 实现 EntityStore Protocol

import copy

from backend.core.utils import utc_now
from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemUpdate
from backend.schemas.persona_schemas import Persona, PersonaUpdate
from backend.schemas.task_schemas import Task, TaskUpdate


class InMemoryEntityStore:
    """使用内存字典存储实体数据。"""

    def __init__(self) -> None:
        self._personas: dict[str, Persona] = {}
        self._tasks: dict[str, Task] = {}
        self._knowledge_items: dict[str, KnowledgeItem] = {}

    # ============================ Persona CRUD ============================ #

    def create_persona(self, persona: Persona) -> Persona:
        self._personas[persona.id] = persona.model_copy(deep=True)
        return persona.model_copy(deep=True)

    def get_persona(self, persona_id: str) -> Persona | None:
        p = self._personas.get(persona_id)
        return p.model_copy(deep=True) if p else None

    def list_personas(self) -> list[Persona]:
        return [p.model_copy(deep=True) for p in self._personas.values()]

    def update_persona(self, persona_id: str, updates: PersonaUpdate) -> Persona | None:
        p = self._personas.get(persona_id)
        if p is None:
            return None
        update_data = updates.model_dump(exclude_none=True)
        updated = p.model_copy(update=update_data)
        updated.updated_at = utc_now()
        self._personas[persona_id] = updated.model_copy(deep=True)
        return updated.model_copy(deep=True)

    def delete_persona(self, persona_id: str) -> bool:
        if persona_id not in self._personas:
            return False
        del self._personas[persona_id]
        return True

    # ============================ Task CRUD ============================ #

    def create_task(self, task: Task) -> Task:
        self._tasks[task.id] = task.model_copy(deep=True)
        return task.model_copy(deep=True)

    def get_task(self, task_id: str) -> Task | None:
        t = self._tasks.get(task_id)
        return t.model_copy(deep=True) if t else None

    def list_tasks(self) -> list[Task]:
        return [t.model_copy(deep=True) for t in self._tasks.values()]

    def update_task(self, task_id: str, updates: TaskUpdate) -> Task | None:
        t = self._tasks.get(task_id)
        if t is None:
            return None
        update_data = updates.model_dump(exclude_none=True)
        updated = t.model_copy(update=update_data)
        updated.updated_at = utc_now()
        self._tasks[task_id] = updated.model_copy(deep=True)
        return updated.model_copy(deep=True)

    def delete_task(self, task_id: str) -> bool:
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True

    # ============================ KnowledgeItem CRUD ============================ #

    def create_knowledge_item(self, item: KnowledgeItem) -> KnowledgeItem:
        self._knowledge_items[item.id] = item.model_copy(deep=True)
        return item.model_copy(deep=True)

    def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        item = self._knowledge_items.get(item_id)
        return item.model_copy(deep=True) if item else None

    def list_knowledge_items(self, source_type: str | None = None) -> list[KnowledgeItem]:
        items = self._knowledge_items.values()
        if source_type is not None:
            items = [i for i in items if i.source_type == source_type]
        return [i.model_copy(deep=True) for i in items]

    def update_knowledge_item(self, item_id: str, updates: KnowledgeItemUpdate) -> KnowledgeItem | None:
        item = self._knowledge_items.get(item_id)
        if item is None:
            return None
        update_data = updates.model_dump(exclude_none=True)
        updated = item.model_copy(update=update_data)
        updated.updated_at = utc_now()
        self._knowledge_items[item_id] = updated.model_copy(deep=True)
        return updated.model_copy(deep=True)

    def delete_knowledge_item(self, item_id: str) -> bool:
        if item_id not in self._knowledge_items:
            return False
        del self._knowledge_items[item_id]
        return True

    # ============================ 通用 ============================ #

    def clear(self) -> None:
        self._personas.clear()
        self._tasks.clear()
        self._knowledge_items.clear()

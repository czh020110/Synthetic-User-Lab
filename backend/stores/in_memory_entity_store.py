from __future__ import annotations

# ============================ 内存实体存储模块 ============================ #
# 模块功能: 使用内存字典存储 Persona/Task/KnowledgeItem，供开发和测试使用
# 模块接口说明: InMemoryEntityStore 实现 EntityStore Protocol

import copy

from backend.core.utils import utc_now
from backend.schemas.guard_config_schemas import GUARD_CONFIG_KEY, GuardConfig
from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemUpdate
from backend.schemas.model_preset_schemas import ModelPreset, ModelPresetUpdate
from backend.schemas.persona_schemas import Persona, PersonaUpdate
from backend.schemas.settings_schemas import FRONTEND_SETTINGS_KEY, FrontendSettings
from backend.schemas.task_schemas import Task, TaskUpdate


class InMemoryEntityStore:
    """使用内存字典存储实体数据。"""

    def __init__(self) -> None:
        self._personas: dict[str, Persona] = {}
        self._tasks: dict[str, Task] = {}
        self._knowledge_items: dict[str, KnowledgeItem] = {}
        self._frontend_settings = FrontendSettings(settings_key=FRONTEND_SETTINGS_KEY)
        self._model_presets: dict[str, ModelPreset] = {}
        self._guard_config = GuardConfig(settings_key=GUARD_CONFIG_KEY)

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
        # 用 exclude_unset 而非 exclude_none：model_preset_id 是可空字段，显式传 null 才能清空
        update_data = updates.model_dump(exclude_unset=True)
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

    # ============================ FrontendSettings ============================ #

    def get_frontend_settings(self) -> FrontendSettings:
        return self._frontend_settings.model_copy(deep=True)

    def upsert_frontend_settings(self, settings: FrontendSettings) -> FrontendSettings:
        self._frontend_settings = settings.model_copy(deep=True)
        return self._frontend_settings.model_copy(deep=True)

    # ============================ ModelPreset CRUD ============================ #

    def create_model_preset(self, preset: ModelPreset) -> ModelPreset:
        # 已存在则不覆盖，与 sqlite/pg ON CONFLICT 行为一致
        if preset.id in self._model_presets:
            return self._model_presets[preset.id].model_copy(deep=True)
        self._model_presets[preset.id] = preset.model_copy(deep=True)
        if preset.is_default:
            for other in self._model_presets.values():
                if other.id != preset.id and other.is_default:
                    other.is_default = False
                    other.updated_at = utc_now()
        return self._model_presets[preset.id].model_copy(deep=True)

    def get_model_preset(self, preset_id: str) -> ModelPreset | None:
        p = self._model_presets.get(preset_id)
        return p.model_copy(deep=True) if p else None

    def list_model_presets(self) -> list[ModelPreset]:
        return [p.model_copy(deep=True) for p in self._model_presets.values()]

    def update_model_preset(self, preset_id: str, updates: ModelPresetUpdate) -> ModelPreset | None:
        p = self._model_presets.get(preset_id)
        if p is None:
            return None
        updated = p.model_copy(update=updates.model_dump(exclude_none=True))
        updated.updated_at = utc_now()
        self._model_presets[preset_id] = updated.model_copy(deep=True)
        return updated.model_copy(deep=True)

    def delete_model_preset(self, preset_id: str) -> bool:
        if preset_id not in self._model_presets:
            return False
        del self._model_presets[preset_id]
        return True

    def set_default_model_preset(self, preset_id: str) -> ModelPreset | None:
        p = self._model_presets.get(preset_id)
        if p is None:
            return None
        for other in self._model_presets.values():
            new_default = other.id == preset_id
            if other.is_default != new_default:
                other.is_default = new_default
                other.updated_at = utc_now()
        return self._model_presets[preset_id].model_copy(deep=True)

    # ============================ GuardConfig ============================ #

    def get_guard_config(self) -> GuardConfig:
        return self._guard_config.model_copy(deep=True)

    def upsert_guard_config(self, config: GuardConfig) -> GuardConfig:
        self._guard_config = config.model_copy(deep=True)
        return self._guard_config.model_copy(deep=True)

    # ============================ 通用 ============================ #

    def clear(self) -> None:
        self._personas.clear()
        self._tasks.clear()
        self._knowledge_items.clear()
        self._model_presets.clear()
        self._frontend_settings = FrontendSettings(settings_key=FRONTEND_SETTINGS_KEY)
        self._guard_config = GuardConfig(settings_key=GUARD_CONFIG_KEY)

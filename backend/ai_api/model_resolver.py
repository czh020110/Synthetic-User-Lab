from __future__ import annotations

# ============================ 运行时模型解析模块 ============================ #
# 模块功能: 按 persona 预设 -> 默认预设 -> env 的优先级解析运行时模型配置
# 模块接口说明: resolve_runtime_model(persona, entity_store) 返回 RuntimeModelConfig

from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.core.config import get_settings
from backend.schemas.persona_schemas import Persona

if TYPE_CHECKING:
    from backend.stores.entity_store_protocol import EntityStore


@dataclass
class RuntimeModelConfig:
    """运行时模型调用所需的最小参数集。"""

    provider: str
    api_key: str
    base_url: str
    model_name: str
    fast_model_name: str


def resolve_runtime_model(persona: Persona | None, entity_store: "EntityStore") -> RuntimeModelConfig:
    """解析运行时模型配置：persona 指定预设 -> 默认预设 -> env 兜底。

    persona 为 None 或其 model_preset_id 无效时，回退到默认预设；无任何预设时回退到 env。
    """

    preset = None
    if persona is not None and persona.model_preset_id:
        preset = entity_store.get_model_preset(persona.model_preset_id)
    if preset is None:
        presets = entity_store.list_model_presets()
        preset = next((p for p in presets if p.is_default), None)
        if preset is None and presets:
            preset = presets[0]

    if preset is not None:
        return RuntimeModelConfig(
            provider=preset.provider,
            api_key=preset.api_key,
            base_url=preset.base_url,
            model_name=preset.model_name,
            fast_model_name=preset.fast_model_name or preset.model_name,
        )

    # env 兜底（首次未 seed 或无预设时）
    settings = get_settings()
    return RuntimeModelConfig(
        provider=settings.model_provider,
        api_key=settings.api_key,
        base_url=settings.base_url,
        model_name=settings.model_name,
        fast_model_name=settings.fast_model_name or settings.model_name,
    )

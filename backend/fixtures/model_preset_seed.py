from __future__ import annotations

# ============================ 模型预设 seed 模块 ============================ #
# 模块功能: 首次启动时从 .env 配置 seed 一个默认模型预设，让开箱即用既有可用模型配置
# 模块接口说明: seed_default_model_preset_if_absent(store) 被 main.py lifespan 调用，幂等

from typing import TYPE_CHECKING

from backend.core.config import get_settings
from backend.schemas.model_preset_schemas import ModelPreset

if TYPE_CHECKING:
    from backend.stores.entity_store_protocol import EntityStore


def seed_default_model_preset_if_absent(store: "EntityStore") -> ModelPreset | None:
    """若没有任何模型预设，从当前 .env 配置创建一个默认预设。

    幂等：已存在预设时直接返回 None，不重复创建。
    仅当 env 的 api_key 非空且 provider 受支持时才 seed，避免把空/占位 key 持久化成
    默认预设而覆盖 env（否则用户后续修 .env 也无法生效）；未支持 provider 交由运行时报错。
    """

    if store.list_model_presets():
        return None

    settings = get_settings()
    # 不持久化空 key（否则该预设会覆盖 env，.env 改 key 也不生效）
    if not settings.api_key:
        return None
    # 未支持 provider 不 seed，避免 Literal 校验在启动期崩溃；运行时 _create_chat_model 会报错
    if settings.model_provider not in {"openai", "dashscope"}:
        return None

    preset = ModelPreset(
        name="默认",
        provider=settings.model_provider,
        api_key=settings.api_key,
        base_url=settings.base_url,
        model_name=settings.model_name,
        fast_model_name=settings.fast_model_name or settings.model_name,
        is_default=True,
    )
    return store.create_model_preset(preset)

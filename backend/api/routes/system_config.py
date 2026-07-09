from __future__ import annotations

# ============================ 系统配置路由模块 ============================ #
# 模块功能: 提供模型预设 CRUD 与破坏性动作关键词库读写接口
# 模块数据流: HTTP 请求 -> EntityStore -> HTTP 响应

from fastapi import APIRouter, HTTPException

from backend.core.utils import utc_now
from backend.schemas.guard_config_schemas import GuardConfig, GuardConfigUpdate
from backend.schemas.model_preset_schemas import (
    ModelPreset,
    ModelPresetCreate,
    ModelPresetUpdate,
)
from backend.schemas.run_schemas import ApiResponse
from backend.stores import get_entity_store

router = APIRouter(prefix="/system", tags=["system"])


def _mask_preset(preset: ModelPreset) -> ModelPreset:
    """返回 api_key 脱敏副本（首尾各 4 位），避免 list/get 接口回显明文 key。"""

    key = preset.api_key
    if not key:
        return preset
    masked = f"{key[:4]}••••{key[-4:]}" if len(key) > 8 else "••••"
    return preset.model_copy(update={"api_key": masked})


# ============================ 模型预设 ============================ #


@router.get("/model-presets", response_model=ApiResponse)
async def list_model_presets() -> ApiResponse:
    """返回所有模型预设列表。"""

    return ApiResponse(data=[_mask_preset(p) for p in get_entity_store().list_model_presets()])


@router.post("/model-presets", response_model=ApiResponse)
async def create_model_preset(payload: ModelPresetCreate) -> ApiResponse:
    """创建新的模型预设。is_default=True 时自动互斥清除其他默认。"""

    preset = ModelPreset(**payload.model_dump())
    created = get_entity_store().create_model_preset(preset)
    return ApiResponse(data=_mask_preset(created))


@router.put("/model-presets/{preset_id}/default", response_model=ApiResponse)
async def set_default_model_preset(preset_id: str) -> ApiResponse:
    """把指定预设设为默认（互斥）。"""

    updated = get_entity_store().set_default_model_preset(preset_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Model preset not found")
    return ApiResponse(data=_mask_preset(updated))


@router.put("/model-presets/{preset_id}", response_model=ApiResponse)
async def update_model_preset(preset_id: str, payload: ModelPresetUpdate) -> ApiResponse:
    """更新指定模型预设（不含 is_default 切换，切换请用 /default）。"""

    updated = get_entity_store().update_model_preset(preset_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Model preset not found")
    return ApiResponse(data=_mask_preset(updated))


@router.delete("/model-presets/{preset_id}", response_model=ApiResponse)
async def delete_model_preset(preset_id: str) -> ApiResponse:
    """删除指定模型预设。禁止删除当前默认预设。"""

    store = get_entity_store()
    preset = store.get_model_preset(preset_id)
    if preset is None:
        raise HTTPException(status_code=404, detail="Model preset not found")
    if preset.is_default:
        raise HTTPException(
            status_code=400,
            detail="不能删除默认预设，请先把其他预设设为默认",
        )
    if not store.delete_model_preset(preset_id):
        raise HTTPException(status_code=404, detail="Model preset not found")
    return ApiResponse(data={"deleted": True})


# ============================ 破坏性动作关键词库 ============================ #


@router.get("/guard-config", response_model=ApiResponse)
async def get_guard_config() -> ApiResponse:
    """返回护栏关键词库；若未保存则返回默认词库。"""

    return ApiResponse(data=get_entity_store().get_guard_config())


@router.put("/guard-config", response_model=ApiResponse)
async def update_guard_config(payload: GuardConfigUpdate) -> ApiResponse:
    """更新护栏关键词库。"""

    store = get_entity_store()
    existing = store.get_guard_config()
    updated = existing.model_copy(update=payload.model_dump(exclude_none=True))
    updated.updated_at = utc_now()
    return ApiResponse(data=store.upsert_guard_config(updated))

from __future__ import annotations

# ============================ Frontend Settings 路由模块 ============================ #
# 模块功能: 提供前端产品化设置的读取与更新接口
# 模块数据流: HTTP 请求 -> EntityStore -> HTTP 响应

from fastapi import APIRouter

from backend.core.utils import utc_now
from backend.schemas.run_schemas import ApiResponse
from backend.schemas.settings_schemas import FrontendSettingsUpdate
from backend.stores import get_entity_store

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/frontend", response_model=ApiResponse)
async def get_frontend_settings() -> ApiResponse:
    """返回前端设置；若未保存则返回默认值。"""

    return ApiResponse(data=get_entity_store().get_frontend_settings())


@router.put("/frontend", response_model=ApiResponse)
async def update_frontend_settings(payload: FrontendSettingsUpdate) -> ApiResponse:
    """更新前端设置。"""

    store = get_entity_store()
    existing = store.get_frontend_settings()
    updated = existing.model_copy(update=payload.model_dump(exclude_none=True))
    updated.updated_at = utc_now()
    return ApiResponse(data=store.upsert_frontend_settings(updated))

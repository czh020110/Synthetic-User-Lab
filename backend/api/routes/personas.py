from __future__ import annotations

# ============================ Persona 路由模块 ============================ #
# 模块功能: 提供 Persona 的 CRUD 接口
# 模块数据流: HTTP 请求 -> EntityStore -> HTTP 响应

from fastapi import APIRouter, HTTPException

from backend.schemas.persona_schemas import Persona, PersonaCreate, PersonaUpdate
from backend.schemas.run_schemas import ApiResponse
from backend.stores import get_entity_store

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("/", response_model=ApiResponse)
async def create_persona(payload: PersonaCreate) -> ApiResponse:
    """创建新的 persona。"""

    persona = Persona(**payload.model_dump())
    created = get_entity_store().create_persona(persona)
    return ApiResponse(data=created)


@router.get("/", response_model=ApiResponse)
async def list_personas() -> ApiResponse:
    """返回所有 persona 列表。"""

    return ApiResponse(data=get_entity_store().list_personas())


@router.get("/{persona_id}", response_model=ApiResponse)
async def get_persona(persona_id: str) -> ApiResponse:
    """返回指定 persona。"""

    persona = get_entity_store().get_persona(persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    return ApiResponse(data=persona)


@router.put("/{persona_id}", response_model=ApiResponse)
async def update_persona(persona_id: str, payload: PersonaUpdate) -> ApiResponse:
    """更新指定 persona。"""

    updated = get_entity_store().update_persona(persona_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    return ApiResponse(data=updated)


@router.delete("/{persona_id}", response_model=ApiResponse)
async def delete_persona(persona_id: str) -> ApiResponse:
    """删除指定 persona。"""

    if not get_entity_store().delete_persona(persona_id):
        raise HTTPException(status_code=404, detail="Persona not found")
    return ApiResponse(data={"deleted": True})

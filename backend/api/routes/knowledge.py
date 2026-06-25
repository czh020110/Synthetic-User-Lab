from __future__ import annotations

# ============================ Knowledge 路由模块 ============================ #
# 模块功能: 提供 KnowledgeItem 的 CRUD 接口
# 模块数据流: HTTP 请求 -> EntityStore -> HTTP 响应

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemCreate, KnowledgeItemUpdate
from backend.schemas.run_schemas import ApiResponse
from backend.stores import get_entity_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/", response_model=ApiResponse)
async def create_knowledge_item(payload: KnowledgeItemCreate) -> ApiResponse:
    """创建新的知识条目。"""

    item = KnowledgeItem(**payload.model_dump())
    created = get_entity_store().create_knowledge_item(item)
    return ApiResponse(data=created)


@router.get("/", response_model=ApiResponse)
async def list_knowledge_items(source_type: str | None = Query(default=None)) -> ApiResponse:
    """返回知识条目列表，可按 source_type 过滤。"""

    return ApiResponse(data=get_entity_store().list_knowledge_items(source_type=source_type))


@router.get("/{item_id}", response_model=ApiResponse)
async def get_knowledge_item(item_id: str) -> ApiResponse:
    """返回指定知识条目。"""

    item = get_entity_store().get_knowledge_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return ApiResponse(data=item)


@router.put("/{item_id}", response_model=ApiResponse)
async def update_knowledge_item(item_id: str, payload: KnowledgeItemUpdate) -> ApiResponse:
    """更新指定知识条目。"""

    updated = get_entity_store().update_knowledge_item(item_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return ApiResponse(data=updated)


@router.delete("/{item_id}", response_model=ApiResponse)
async def delete_knowledge_item(item_id: str) -> ApiResponse:
    """删除指定知识条目。"""

    if not get_entity_store().delete_knowledge_item(item_id):
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return ApiResponse(data={"deleted": True})

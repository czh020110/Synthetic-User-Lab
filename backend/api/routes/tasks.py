from __future__ import annotations

# ============================ Task 路由模块 ============================ #
# 模块功能: 提供 Task 的 CRUD 接口
# 模块数据流: HTTP 请求 -> EntityStore -> HTTP 响应

from fastapi import APIRouter, HTTPException

from backend.schemas.run_schemas import ApiResponse
from backend.schemas.task_schemas import Task, TaskCreate, TaskUpdate
from backend.stores import get_entity_store

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=ApiResponse)
async def create_task(payload: TaskCreate) -> ApiResponse:
    """创建新的 task。"""

    task = Task(**payload.model_dump())
    created = get_entity_store().create_task(task)
    return ApiResponse(data=created)


@router.get("/", response_model=ApiResponse)
async def list_tasks() -> ApiResponse:
    """返回所有 task 列表。"""

    return ApiResponse(data=get_entity_store().list_tasks())


@router.get("/{task_id}", response_model=ApiResponse)
async def get_task(task_id: str) -> ApiResponse:
    """返回指定 task。"""

    task = get_entity_store().get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return ApiResponse(data=task)


@router.put("/{task_id}", response_model=ApiResponse)
async def update_task(task_id: str, payload: TaskUpdate) -> ApiResponse:
    """更新指定 task。"""

    updated = get_entity_store().update_task(task_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return ApiResponse(data=updated)


@router.delete("/{task_id}", response_model=ApiResponse)
async def delete_task(task_id: str) -> ApiResponse:
    """删除指定 task。"""

    if not get_entity_store().delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return ApiResponse(data={"deleted": True})

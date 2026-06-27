from __future__ import annotations

# ============================ 正式 Run 路由模块 ============================ #
# 模块功能: 提供引用 persona_id/task_id 的正式 run 启动和查询接口
# 模块数据流: HTTP 请求 -> EntityStore 解析 -> RunStore 创建 -> 后台执行 -> HTTP 响应
# 模块接口说明: start/status/steps/report 接口覆盖正式 run 闭环查询面

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from backend.core.config import get_settings
from backend.graph.formal_run_graph import run_formal_workflow
from backend.schemas.run_schemas import ApiResponse, FormalRunRequest, RunRecord, RunRequest
from backend.stores import get_entity_store, get_run_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runs", tags=["runs"])
_background_tasks: set[asyncio.Task] = set()


def _track_background_task(run_id: str, task: asyncio.Task) -> None:
    """保持后台 task 强引用，并在异常/取消时自动将 run 标记为 failed。"""
    _background_tasks.add(task)

    def handle_done(done_task: asyncio.Task) -> None:
        _background_tasks.discard(done_task)
        store = get_run_store()
        status = store.get_status(run_id)
        if status is not None and status.status in {"succeeded", "failed"}:
            return
        if done_task.cancelled():
            store.fail_run(run_id, "后台任务被取消。")
            return
        exc = done_task.exception()
        if exc is not None:
            logger.error(
                "formal run background task failed, run_id=%s",
                run_id,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            store.fail_run(run_id, f"{type(exc).__name__}: {exc}")

    task.add_done_callback(handle_done)


@router.post("/start", response_model=ApiResponse)
async def start_formal_run(request: Request, payload: FormalRunRequest) -> ApiResponse:
    """创建正式 run 并异步执行。需要提供 persona_id 和 task_id。"""

    entity_store = get_entity_store()
    run_store = get_run_store()

    # 解析 persona 和 task
    persona = entity_store.get_persona(payload.persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona not found: {payload.persona_id}")
    task = entity_store.get_task(payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {payload.task_id}")

    settings = get_settings()
    run_id = str(uuid4())
    app_base_url = str(request.base_url).rstrip("/")
    run_request = RunRequest(run_name=payload.run_name, headless=payload.headless)

    record = RunRecord(run_id=run_id, request=run_request, persona=persona, task=task)
    run_store.create_run(record)

    task_coro = asyncio.create_task(
        run_formal_workflow(
            run_id=run_id,
            request=run_request,
            app_base_url=app_base_url,
            screenshot_dir=settings.screenshot_dir,
            persona=persona,
            task=task,
            record=record,
        )
    )
    _track_background_task(run_id, task_coro)
    return ApiResponse(data={"run_id": run_id, "status": "queued"})


@router.get("/", response_model=ApiResponse)
async def list_runs() -> ApiResponse:
    """返回所有 run 的状态列表。"""

    store = get_run_store()
    run_ids = store.list_run_ids()
    statuses = []
    for rid in run_ids:
        s = store.get_status(rid)
        if s is not None:
            statuses.append(s)
    return ApiResponse(data=statuses)


@router.get("/{run_id}", response_model=ApiResponse)
async def get_run_status(run_id: str) -> ApiResponse:
    """返回 run 当前状态。"""

    status = get_run_store().get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return ApiResponse(data=status)


@router.get("/{run_id}/steps", response_model=ApiResponse)
async def get_run_steps(run_id: str) -> ApiResponse:
    """返回 run 全部步骤日志。"""

    steps = get_run_store().get_steps(run_id)
    if steps is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return ApiResponse(data=steps)


@router.get("/{run_id}/report", response_model=ApiResponse)
async def get_run_report(run_id: str) -> ApiResponse:
    """返回 run 最终报告。"""

    store = get_run_store()
    report = store.get_report(run_id)
    if report is None:
        record = store.get_record(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Run not found")
        raise HTTPException(status_code=409, detail="Run report is not ready")
    return ApiResponse(data=report)


@router.get("/{run_id}/report/markdown", response_model=ApiResponse)
async def get_run_report_markdown(run_id: str) -> ApiResponse:
    """返回 run 最终报告的 Markdown 渲染。"""

    store = get_run_store()
    report = store.get_report(run_id)
    if report is None:
        record = store.get_record(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Run not found")
        raise HTTPException(status_code=409, detail="Run report is not ready")
    from backend.analysis.report_renderer import render_report_markdown

    return ApiResponse(data={"markdown": render_report_markdown(report)})

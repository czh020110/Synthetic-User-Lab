from __future__ import annotations

# ============================ Demo Run 路由模块 ============================ #
# 使用技术栈: Python / FastAPI
# 模块功能: 提供启动 demo run、查询状态、步骤与报告的接口
# 模块数据流: HTTP 请求 -> 内存记录/后台执行 -> HTTP 响应
# 模块接口说明: start/status/steps/report 四个接口覆盖最小 run 闭环查询面

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from backend.core.config import get_settings
from backend.graph.demo_run_graph import create_demo_placeholder_record, run_demo_workflow
from backend.schemas.run_schemas import ApiResponse, RunRequest
from backend.stores import get_run_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runs/demo", tags=["demo-runs"])
_background_tasks: set[asyncio.Task] = set()
run_store = get_run_store()


def _track_background_task(run_id: str, task: asyncio.Task) -> None:
    """保持后台 task 强引用，并在异常/取消时自动将 run 标记为 failed。"""
    _background_tasks.add(task)

    def handle_done(done_task: asyncio.Task) -> None:
        _background_tasks.discard(done_task)
        status = run_store.get_status(run_id)
        if status is not None and status.status in {"succeeded", "failed"}:
            return
        if done_task.cancelled():
            run_store.fail_run(run_id, "后台任务被取消。")
            return
        exc = done_task.exception()
        if exc is not None:
            logger.error(
                "demo run background task failed, run_id=%s",
                run_id,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            run_store.fail_run(run_id, f"{type(exc).__name__}: {exc}")

    task.add_done_callback(handle_done)


@router.get("/health", response_model=ApiResponse)
async def health_check() -> ApiResponse:
    """返回服务健康状态。"""

    return ApiResponse(data={"service": "synthetic-user-lab", "status": "ok"})


@router.post("/start", response_model=ApiResponse)
async def start_demo_run(request: Request, payload: RunRequest) -> ApiResponse:
    """创建 demo run 并异步执行。"""

    settings = get_settings()
    run_id = str(uuid4())
    app_base_url = str(request.base_url).rstrip("/")
    placeholder_record = create_demo_placeholder_record(
        run_id=run_id,
        request=payload,
        app_base_url=app_base_url,
    )
    run_store.create_run(placeholder_record)
    task = asyncio.create_task(
        run_demo_workflow(
            run_id=run_id,
            request=payload,
            app_base_url=app_base_url,
            screenshot_dir=settings.screenshot_dir,
        )
    )
    _track_background_task(run_id, task)
    return ApiResponse(data={"run_id": run_id, "status": "queued"})


@router.get("/{run_id}", response_model=ApiResponse)
async def get_demo_run_status(run_id: str) -> ApiResponse:
    """返回 demo run 当前状态。"""

    status = run_store.get_status(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return ApiResponse(data=status)


@router.get("/{run_id}/steps", response_model=ApiResponse)
async def get_demo_run_steps(run_id: str) -> ApiResponse:
    """返回 demo run 全部步骤日志。"""

    steps = run_store.get_steps(run_id)
    if steps is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return ApiResponse(data=steps)


@router.get("/{run_id}/report", response_model=ApiResponse)
async def get_demo_run_report(run_id: str) -> ApiResponse:
    """返回 demo run 最终报告。"""

    report = run_store.get_report(run_id)
    if report is None:
        record = run_store.get_record(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Run not found")
        raise HTTPException(status_code=409, detail="Run report is not ready")
    return ApiResponse(data=report)


@router.get("/{run_id}/report/markdown", response_model=ApiResponse)
async def get_demo_run_report_markdown(run_id: str) -> ApiResponse:
    """返回 demo run 最终报告的 Markdown 渲染。"""

    report = run_store.get_report(run_id)
    if report is None:
        record = run_store.get_record(run_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Run not found")
        raise HTTPException(status_code=409, detail="Run report is not ready")
    from backend.analysis.report_renderer import render_report_markdown
    return ApiResponse(data={"markdown": render_report_markdown(report)})

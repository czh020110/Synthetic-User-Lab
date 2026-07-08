from __future__ import annotations

# ============================ API 路由聚合模块 ============================ #
# 模块功能: 聚合所有 API 路由
# 模块数据流: FastAPI app -> include_router(api_router)
# 模块接口说明: api_router 为主路由入口

from fastapi import APIRouter

from backend.api.routes.demo_runs import router as demo_runs_router
from backend.api.routes.knowledge import router as knowledge_router
from backend.api.routes.personas import router as personas_router
from backend.api.routes.runs import router as runs_router
from backend.api.routes.screenshots import router as screenshots_router
from backend.api.routes.settings import router as settings_router
from backend.api.routes.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(demo_runs_router)
api_router.include_router(personas_router)
api_router.include_router(tasks_router)
api_router.include_router(knowledge_router)
api_router.include_router(runs_router)
api_router.include_router(settings_router)
api_router.include_router(screenshots_router)

from __future__ import annotations

# ============================ API 路由聚合模块 ============================ #
# 使用技术栈: Python / FastAPI
# 模块功能: 聚合健康检查与 demo run 路由
# 模块数据流: FastAPI app -> include_router(api_router)
# 模块接口说明: api_router 为主路由入口

from fastapi import APIRouter

from backend.api.routes.demo_runs import router as demo_runs_router

api_router = APIRouter()
api_router.include_router(demo_runs_router)

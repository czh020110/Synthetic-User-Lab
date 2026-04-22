from __future__ import annotations

# ============================ FastAPI 应用入口模块 ============================ #
# 使用技术栈: Python / FastAPI
# 模块功能: 创建应用实例、挂载 API 与 Demo 页面静态资源
# 模块数据流: Settings -> FastAPI app -> Router / StaticFiles
# 模块接口说明: app 为服务主入口

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_prefix)
app.mount("/demo", StaticFiles(directory=settings.demo_site_dir, html=True), name="demo")

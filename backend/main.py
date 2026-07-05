from __future__ import annotations

# ============================ FastAPI 应用入口模块 ============================ #
# 使用技术栈: Python / FastAPI
# 模块功能: 创建应用实例、挂载 API 与 Demo 页面静态资源
# 模块数据流: Settings -> FastAPI app -> Router / StaticFiles
# 模块接口说明: app 为服务主入口
# 初始化说明: run_store 在模块导入时由 get_run_store() 创建（含建库建表），
#   lifespan 负责启动时 seed demo 实体，关闭时释放连接

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：seed demo persona/task 到 EntityStore（幂等，已存在则跳过）
    from backend.graph.demo_run_graph import build_demo_persona, build_demo_task
    from backend.stores import get_entity_store

    entity_store = get_entity_store()
    demo_persona = build_demo_persona()
    if entity_store.get_persona(demo_persona.id) is None:
        entity_store.create_persona(demo_persona)
    demo_task = build_demo_task(str(settings.app_base_url))
    if entity_store.get_task(demo_task.id) is None:
        entity_store.create_task(demo_task)

    yield

    # 关闭：释放数据库连接并重置存储单例
    from backend.stores import _reset_entity_store, _reset_run_store

    _reset_run_store()
    _reset_entity_store()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)
app.mount("/demo", StaticFiles(directory=settings.demo_site_dir, html=True), name="demo")
app.mount("/site", StaticFiles(directory=settings.test_site_dir, html=True), name="test_site")

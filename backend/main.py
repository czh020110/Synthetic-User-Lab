from __future__ import annotations

# ============================ FastAPI 应用入口模块 ============================ #
# 使用技术栈: Python / FastAPI
# 模块功能: 创建应用实例、挂载 API 与测试站点静态资源
# 模块数据流: Settings -> FastAPI app -> Router / StaticFiles
# 模块接口说明: app 为服务主入口
# 初始化说明: lifespan 负责启动时 seed MVP 样例实体，关闭时释放 store 连接/连接池

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：seed MVP 样例 persona/task 到 EntityStore（幂等，已存在则跳过）
    from backend.api.routes.runs import shutdown_background_tasks as shutdown_formal_background_tasks
    from backend.fixtures.mvp_samples import seed_mvp_samples_if_absent
    from backend.stores import _reset_entity_store, _reset_run_store, get_entity_store

    seed_mvp_samples_if_absent(get_entity_store())

    yield

    # 关闭：先等待后台 run task 收尾，再释放数据库连接与连接池
    await shutdown_formal_background_tasks()
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

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
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.router import api_router
from backend.core.config import get_settings

settings = get_settings()


# 仅托管前端 SPA：对未命中静态文件的 GET 请求回退到 index.html，
# 让 react-router 的客户端路由（如 /runs/new）刷新不 404。
# /api /site /demo 由下方先注册的路由/挂载接管，不会被这里拦截。
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (StarletteHTTPException, RuntimeError):
            return await super().get_response("index.html", scope)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：seed MVP 样例 persona/task 到 EntityStore（幂等，已存在则跳过）
    from backend.api.routes.runs import shutdown_background_tasks as shutdown_formal_background_tasks
    from backend.fixtures.model_preset_seed import seed_default_model_preset_if_absent
    from backend.fixtures.mvp_samples import seed_mvp_samples_if_absent
    from backend.stores import _reset_entity_store, _reset_run_store, get_entity_store

    entity_store = get_entity_store()
    seed_mvp_samples_if_absent(entity_store)
    seed_default_model_preset_if_absent(entity_store)

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

# 容器内托管前端构建产物（本地开发 frontend_dir 为 None，仍走 vite dev 5173 + proxy）。
# 必须在 /api /site /demo 之后挂载，作为 catch-all 兜底。
if settings.frontend_dir is not None:
    app.mount("/", SPAStaticFiles(directory=settings.frontend_dir, html=True), name="frontend")

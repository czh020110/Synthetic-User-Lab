from __future__ import annotations

# ============================ 配置模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 统一管理 FastAPI、Demo 页面与截图目录配置
# 模块数据流: 环境变量 -> Settings -> 应用入口、图编排、执行器
# 模块接口说明: get_settings() 返回全局配置对象

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from backend.ai_api.provider_router import BASE_DIR, get_model_router, load_dotenv


class Settings(BaseModel):
    """保存当前项目运行所需的最小配置。"""

    app_name: str
    app_env: str
    api_prefix: str
    app_host: str
    app_port: int
    app_base_url: str
    browser_headless: bool
    run_step_limit: int
    demo_site_dir: Path
    screenshot_dir: Path
    custom_system_prompt: str
    model_provider: str
    base_url: str
    api_key: str
    model_name: str
    fast_model_name: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回全局配置对象。只有get settings的时候才会加载环境变量配置"""

    load_dotenv()
    model_router = get_model_router()
    api_prefix = os.getenv("SYNTHETIC_USER_LAB_API_PREFIX", "/api/v1")
    api_prefix = api_prefix if api_prefix.startswith("/") else f"/{api_prefix}"
    settings = Settings(
        app_name=os.getenv("SYNTHETIC_USER_LAB_APP_NAME", "Synthetic User Lab"),
        app_env=os.getenv("SYNTHETIC_USER_LAB_ENV", "development"),
        api_prefix=api_prefix,
        app_host=os.getenv("SYNTHETIC_USER_LAB_HOST", "127.0.0.1"),
        app_port=int(os.getenv("SYNTHETIC_USER_LAB_PORT", "8000")),
        app_base_url=os.getenv("SYNTHETIC_USER_LAB_BASE_URL", "http://127.0.0.1:8000"),
        browser_headless=os.getenv("SYNTHETIC_USER_LAB_HEADLESS", "true").lower() != "false",
        run_step_limit=int(os.getenv("SYNTHETIC_USER_LAB_RUN_STEP_LIMIT", "8")),
        demo_site_dir=BASE_DIR / "backend" / "fixtures" / "demo_site",
        screenshot_dir=BASE_DIR / "screenshots",
        custom_system_prompt=os.getenv("CUSTOM_SYSTEM_PROMPT", ""),
        model_provider=model_router.model_provider,
        base_url=model_router.base_url,
        api_key=model_router.api_key,
        model_name=model_router.model_name,
        fast_model_name=model_router.fast_model_name,
    )
    settings.demo_site_dir.mkdir(parents=True, exist_ok=True)
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
    return settings

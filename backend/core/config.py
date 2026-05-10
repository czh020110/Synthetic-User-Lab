from __future__ import annotations

# ============================ 配置模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 统一管理 FastAPI、Demo 页面与截图目录配置
# 模块数据流: 环境变量 -> Settings -> 应用入口、图编排、执行器
# 模块接口说明: get_settings() 返回全局配置对象

import os
from functools import lru_cache  # 给 get_settings() 做缓存，避免重复创建配置对象
from pathlib import Path

from pydantic import BaseModel

from backend.ai_api.provider_router import load_dotenv, BASE_DIR, get_model_router

load_dotenv()
model_router = get_model_router()

# 系统或脚本或编辑器ide的环境变量
class Settings(BaseModel):
    """保存当前项目运行所需的最小配置。"""

    app_name: str = os.getenv("SYNTHETIC_USER_LAB_APP_NAME", "Synthetic User Lab")
    app_env: str = os.getenv("SYNTHETIC_USER_LAB_ENV", "development")
    api_prefix: str = os.getenv("SYNTHETIC_USER_LAB_API_PREFIX", "/api/v1")
    app_host: str = os.getenv("SYNTHETIC_USER_LAB_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("SYNTHETIC_USER_LAB_PORT", "8000"))
    app_base_url: str = os.getenv("SYNTHETIC_USER_LAB_BASE_URL", "http://127.0.0.1:8000")
    browser_headless: bool = os.getenv("SYNTHETIC_USER_LAB_HEADLESS", "true").lower() != "false"
    run_step_limit: int = int(os.getenv("SYNTHETIC_USER_LAB_RUN_STEP_LIMIT", "8"))
    demo_site_dir: Path = BASE_DIR / "backend" / "fixtures" / "demo_site"
    screenshot_dir: Path = BASE_DIR / "screenshots"
    # openai模型配置
    custom_system_prompt : str = os.getenv("CUSTOM_SYSTEM_PROMPT", "")
    model_provider : str = model_router.model_provider
    base_url: str = model_router.base_url
    api_key: str = model_router.api_key
    model_name: str = model_router.model_name
    fast_model_name: str = model_router.fast_model_name
@lru_cache(maxsize=1)  # 进程只保留一个settings实例
def get_settings() -> Settings:
    """返回全局配置对象。"""

    settings = Settings()
    settings.api_prefix = settings.api_prefix if settings.api_prefix.startswith("/") else f"/{settings.api_prefix}"
    # .mkdir: pathlib.Path 对象的方法
    settings.demo_site_dir.mkdir(parents=True, exist_ok=True)  # 确保demo目录存在
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)  # 确保截图目录存在
    return settings

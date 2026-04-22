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

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    """保存当前项目运行所需的最小配置。"""

    app_name: str = "Synthetic User Lab"
    app_env: str = os.getenv("SYNTHETIC_USER_LAB_ENV", "development")
    api_prefix: str = "/api/v1"
    app_host: str = os.getenv("SYNTHETIC_USER_LAB_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("SYNTHETIC_USER_LAB_PORT", "8000"))
    app_base_url: str = os.getenv("SYNTHETIC_USER_LAB_BASE_URL", "http://127.0.0.1:8000")
    browser_headless: bool = os.getenv("SYNTHETIC_USER_LAB_HEADLESS", "true").lower() != "false"
    run_step_limit: int = 8
    demo_site_dir: Path = BASE_DIR / "backend" / "fixtures" / "demo_site"
    screenshot_dir: Path = BASE_DIR / "screenshots"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回全局配置对象。"""

    settings = Settings()
    settings.demo_site_dir.mkdir(parents=True, exist_ok=True)
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
    return settings

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

BASE_DIR = Path(__file__).resolve().parents[2]  # 计算根项目绝对路径(0当前父目录,1往上.2再往上)
# 等价于:BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# /backend/core/config.py

# 系统或脚本或编辑器ide的环境变量
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


@lru_cache(maxsize=1)  # 进程只保留一个settings实例
def get_settings() -> Settings:
    """返回全局配置对象。"""

    settings = Settings()
    # .mkdir: pathlib.Path 对象的方法
    settings.demo_site_dir.mkdir(parents=True, exist_ok=True)  # 确保demo目录存在
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)  # 确保截图目录存在
    return settings

from __future__ import annotations

# ============================ 公共工具模块 ============================ #
# 模块功能: 提供项目级通用工具函数

from datetime import datetime, timezone


def utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc)

from __future__ import annotations

# ============================ GuardConfig 数据模型模块 ============================ #
# 模块功能: 定义破坏性动作关键词库实体及其更新请求模型
# 模块接口说明: GuardConfig 供 API、存储层和 action_guard 使用

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from backend.core.utils import utc_now
from backend.fixtures.guard_defaults import (
    DEFAULT_DESTRUCTIVE_KEYWORDS,
    DEFAULT_SENSITIVE_KEYWORDS,
)

GUARD_CONFIG_KEY = "guard"


class GuardConfig(BaseModel):
    """描述破坏性动作护栏的可编辑关键词库。

    destructive_keywords 命中 click 选择器时阻断；sensitive_keywords 命中 fill 选择器时阻断。
    未显式保存时返回 guard_defaults 中的默认词库。
    """

    settings_key: str = GUARD_CONFIG_KEY
    destructive_keywords: list[str] = Field(
        default_factory=lambda: list(DEFAULT_DESTRUCTIVE_KEYWORDS)
    )
    sensitive_keywords: list[str] = Field(
        default_factory=lambda: list(DEFAULT_SENSITIVE_KEYWORDS)
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GuardConfigUpdate(BaseModel):
    """更新关键词库的请求体。字段为 None 时表示不更新。"""

    destructive_keywords: list[str] | None = None
    sensitive_keywords: list[str] | None = None

    @field_validator("destructive_keywords", "sensitive_keywords", mode="after")
    @classmethod
    def _drop_empty_keywords(cls, v: list[str] | None) -> list[str] | None:
        # 空字符串关键词会让 re.search('', text) 命中任意 selector，静默阻断全部动作，必须剔除
        if v is None:
            return None
        return [kw for kw in v if kw and kw.strip()]

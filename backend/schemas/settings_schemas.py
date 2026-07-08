from __future__ import annotations

# ============================ FrontendSettings 数据模型模块 ============================ #
# 模块功能: 定义前端设置实体及其更新请求模型
# 模块接口说明: FrontendSettings 供 API、存储层和前端设置页使用

from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

from backend.core.utils import utc_now

ThemeMode: TypeAlias = Literal["light", "dark", "auto"]
LocaleCode: TypeAlias = Literal["zh-CN", "en-US"]

FRONTEND_SETTINGS_KEY = "frontend"


class FrontendSettings(BaseModel):
    """描述当前前端产品化界面所需的用户设置。"""

    settings_key: str = FRONTEND_SETTINGS_KEY
    theme: ThemeMode = "light"
    locale: LocaleCode = "zh-CN"
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    default_headless: bool = True
    auto_refresh: bool = True
    refresh_interval_ms: int = Field(default=5000, ge=1000, le=60000)
    default_run_name: str = Field(default="run", min_length=1, max_length=100)
    default_max_steps: int = Field(default=30, ge=1, le=50)
    email_notifications: bool = True
    notify_run_complete: bool = True
    notify_run_failed: bool = True
    notify_system_error: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class FrontendSettingsUpdate(BaseModel):
    """更新前端设置的请求体。字段为 None 时表示不更新。"""

    theme: ThemeMode | None = None
    locale: LocaleCode | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    date_format: str | None = Field(default=None, min_length=1, max_length=50)
    default_headless: bool | None = None
    auto_refresh: bool | None = None
    refresh_interval_ms: int | None = Field(default=None, ge=1000, le=60000)
    default_run_name: str | None = Field(default=None, min_length=1, max_length=100)
    default_max_steps: int | None = Field(default=None, ge=1, le=50)
    email_notifications: bool | None = None
    notify_run_complete: bool | None = None
    notify_run_failed: bool | None = None
    notify_system_error: bool | None = None

from __future__ import annotations

# ============================ Task 数据模型模块 ============================ #
# 模块功能: 定义 Task 实体、ActionName 类型别名及其创建/更新请求模型
# 模块接口说明: Task 和 ActionName 作为独立实体供 API、存储层和 run 图使用

from datetime import datetime
from typing import Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from backend.core.utils import utc_now

ActionName: TypeAlias = Literal[
    "navigate", "click", "fill", "wait",
    "press", "scroll", "upload", "select",
    "hover", "check", "uncheck", "dblclick",
    "drag", "ask_for_help", "abandon",
]

RiskLevel: TypeAlias = Literal["low", "medium", "high"]


class Task(BaseModel):
    """描述任务实体。"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "完成页面任务"
    description: str = "进入页面后，根据页面提示完成当前任务；如页面要求填写表单，可自行生成合理的测试数据。"
    start_url: str
    success_criteria: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=8, ge=1, le=50)
    allowed_actions: list[ActionName] = Field(default_factory=lambda: ["navigate", "click", "fill", "wait"])
    risk_level: RiskLevel = "low"
    destructive_action_allowed: bool = False  # 是否允许执行"破坏性动作":删除/提交/发布/支付等
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TaskCreate(BaseModel):
    """创建 Task 的请求体。"""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    start_url: str = Field(..., min_length=1)
    success_criteria: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=8, ge=1, le=50)
    allowed_actions: list[ActionName] = Field(default_factory=lambda: ["navigate", "click", "fill", "wait"])
    risk_level: RiskLevel = Field(default="low")
    destructive_action_allowed: bool = False

    @field_validator("start_url")
    @classmethod
    def validate_start_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("start_url must start with http:// or https://")
        return v


class TaskUpdate(BaseModel):
    """更新 Task 的请求体。字段为 None 时表示不更新。"""

    name: str | None = None
    description: str | None = None
    start_url: str | None = None
    success_criteria: list[str] | None = None
    max_steps: int | None = None
    allowed_actions: list[ActionName] | None = None
    risk_level: RiskLevel | None = None
    destructive_action_allowed: bool | None = None

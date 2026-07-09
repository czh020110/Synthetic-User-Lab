from __future__ import annotations

# ============================ Persona 数据模型模块 ============================ #
# 模块功能: 定义 Persona 实体及其创建/更新请求模型
# 模块接口说明: Persona 作为独立实体供 API、存储层和 run 图使用

from datetime import datetime
from typing import Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.utils import utc_now

SkillLevel: TypeAlias = Literal["newbie", "intermediate", "expert"]
PatienceLevel: TypeAlias = Literal["low", "medium", "high"]
RiskPreference: TypeAlias = Literal["low", "medium", "high"]


class Persona(BaseModel):
    """描述用户画像实体。"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "默认测试用户"
    description: str = "会按照页面主路径逐步完成任务，不进行高风险操作。"
    skill_level: SkillLevel = "newbie"
    patience_level: PatienceLevel = "medium"
    risk_preference: RiskPreference = "low"
    model_preset_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PersonaCreate(BaseModel):
    """创建 Persona 的请求体。"""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    skill_level: SkillLevel = Field(default="newbie")
    patience_level: PatienceLevel = Field(default="medium")
    risk_preference: RiskPreference = Field(default="low")
    model_preset_id: str | None = None


class PersonaUpdate(BaseModel):
    """更新 Persona 的请求体。字段为 None 时表示不更新。"""

    name: str | None = None
    description: str | None = None
    skill_level: SkillLevel | None = None
    patience_level: PatienceLevel | None = None
    risk_preference: RiskPreference | None = None
    model_preset_id: str | None = None

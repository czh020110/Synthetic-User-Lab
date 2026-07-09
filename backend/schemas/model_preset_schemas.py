from __future__ import annotations

# ============================ ModelPreset 数据模型模块 ============================ #
# 模块功能: 定义模型预设实体及其创建/更新请求模型，供系统配置页与运行时模型解析使用
# 模块接口说明: ModelPreset 作为独立实体供 API、存储层和 model_resolver 使用

from datetime import datetime
from typing import Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.utils import utc_now

ModelProvider: TypeAlias = Literal["openai", "dashscope"]


class ModelPreset(BaseModel):
    """描述一个可复用的模型配置预设。

    provider/api_key/base_url/model_name/fast_model_name 共同决定一次 LLM 调用参数；
    is_default=True 的预设作为全局默认，persona 未指定预设时使用它。
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    provider: ModelProvider
    api_key: str = ""
    base_url: str = ""
    model_name: str
    fast_model_name: str = ""
    is_default: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ModelPresetCreate(BaseModel):
    """创建模型预设的请求体。"""

    name: str = Field(..., min_length=1, max_length=100)
    provider: ModelProvider
    api_key: str = Field(default="", max_length=500)
    base_url: str = Field(default="", max_length=500)
    model_name: str = Field(..., min_length=1, max_length=200)
    fast_model_name: str = Field(default="", max_length=200)
    is_default: bool = False


class ModelPresetUpdate(BaseModel):
    """更新模型预设的请求体。字段为 None 时表示不更新。

    不含 is_default：默认预设的切换由 set_default_model_preset 专门处理，避免多预设同设默认。
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    provider: ModelProvider | None = None
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=500)
    model_name: str | None = Field(default=None, min_length=1, max_length=200)
    fast_model_name: str | None = Field(default=None, max_length=200)

from __future__ import annotations

# ============================ Knowledge 数据模型模块 ============================ #
# 模块功能: 定义 KnowledgeItem 实体及其创建/更新请求模型
# 模块接口说明: KnowledgeItem 供 API、存储层和检索层使用

from datetime import datetime
from typing import Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.core.utils import utc_now

RetrievalSourceType: TypeAlias = Literal["product_knowledge", "failure_case"]


class KnowledgeItem(BaseModel):
    """描述知识条目实体。"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_type: RetrievalSourceType
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    keywords: list[str] = Field(default_factory=list)
    source_ref: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class KnowledgeItemCreate(BaseModel):
    """创建 KnowledgeItem 的请求体。"""

    source_type: RetrievalSourceType
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    keywords: list[str] = Field(default_factory=list)
    source_ref: str = ""


class KnowledgeItemUpdate(BaseModel):
    """更新 KnowledgeItem 的请求体。字段为 None 时表示不更新。"""

    title: str | None = None
    content: str | None = None
    keywords: list[str] | None = None
    source_ref: str | None = None

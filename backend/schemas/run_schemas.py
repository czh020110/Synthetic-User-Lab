from __future__ import annotations

# ============================ Run 数据模型模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 定义 demo run 的请求、页面观察、动作、步骤日志与报告结构
# 模块数据流: API 请求 -> LangGraph 状态 -> 执行结果/报告 -> API 响应
# 模块接口说明: 各 BaseModel 作为模块间统一输入输出结构

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ActionName = Literal["navigate", "click", "fill", "wait"]
RunStatus = Literal["queued", "running", "succeeded", "failed"]
ValidationStatus = Literal["running", "succeeded", "failed"]


def utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc)


class ApiResponse(BaseModel):
    """统一 API 响应结构。"""

    success: bool = True
    message: str = "ok"
    data: Any | None = None


class DemoPersona(BaseModel):
    """描述当前 demo 使用的固定 persona。"""

    id: str = "demo-persona-newbie"
    name: str = "新手体验用户"
    description: str = "会按照页面主路径逐步完成任务，不进行高风险操作。"
    skill_level: str = "newbie"
    patience_level: str = "medium"
    risk_preference: str = "low"


class DemoTask(BaseModel):
    """描述当前 demo 使用的固定任务。"""

    id: str = "demo-task-onboarding"
    name: str = "完成体验引导表单"
    description: str = "进入 demo 页面，打开表单，填写信息并完成提交。"
    start_url: str
    success_text: str = "提交成功"
    max_steps: int = 8
    allowed_actions: list[ActionName] = Field(default_factory=lambda: ["navigate", "click", "fill", "wait"])
    risk_level: str = "low"
    destructive_action_allowed: bool = False


class RunRequest(BaseModel):
    """定义启动 demo run 的请求体。"""

    run_name: str = "demo-run"
    expected_user_name: str = "Synthetic User"
    expected_email: str = "synthetic.user@example.com"
    headless: bool | None = None
    operator_note: str = ""


class ObservedElement(BaseModel):
    """描述可交互元素摘要。"""

    text: str = ""
    selector: str = ""


class FormFieldState(BaseModel):
    """描述表单字段摘要。"""

    name: str = ""
    selector: str = ""
    value: str = ""


class ObservedPageState(BaseModel):
    """描述页面观察结果。"""

    current_url: str
    title: str
    visible_text_summary: str
    clickable_elements: list[ObservedElement] = Field(default_factory=list)
    form_fields: list[FormFieldState] = Field(default_factory=list)
    error_messages: list[str] = Field(default_factory=list)


class ActionInput(BaseModel):
    """描述下一步受控动作。"""

    action: ActionName
    target: str
    value: str | None = None
    reason: str = ""


class ExecutionResult(BaseModel):
    """描述动作执行结果。"""

    action: ActionName
    success: bool
    detail: str
    screenshot_path: str | None = None
    current_url_after_action: str | None = None
    error_message: str | None = None


class ValidationResult(BaseModel):
    """描述当前步骤的验证结论。"""

    status: ValidationStatus
    should_stop: bool
    progress_summary: str
    friction_signals: list[str] = Field(default_factory=list)
    detected_success: bool = False
    detected_error: bool = False


class StepLog(BaseModel):
    """描述单步执行日志。"""

    step_index: int
    observed_page_state: ObservedPageState
    decided_action: ActionInput
    execution_result: ExecutionResult
    validation_result: ValidationResult


class RunReport(BaseModel):
    """描述最终 run 报告。"""

    run_id: str
    status: RunStatus
    summary: str
    success: bool
    persona: DemoPersona
    task: DemoTask
    total_steps: int
    friction_signals: list[str] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    next_recommendations: list[str] = Field(default_factory=list)


class RunRecord(BaseModel):
    """描述内存中的运行记录。"""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: RunStatus = "queued"
    request: RunRequest
    persona: DemoPersona
    task: DemoTask
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    error_message: str | None = None


class RunStatusResponse(BaseModel):
    """描述运行状态接口返回值。"""

    run_id: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None

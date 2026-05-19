from __future__ import annotations

# ============================ Run 数据模型模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 定义 run 的请求、页面观察、动作、步骤日志与报告结构
# 模块数据流: API 请求 -> LangGraph 状态 -> 执行结果/报告 -> API 响应
# 模块接口说明: 各 BaseModel 作为模块间统一输入输出结构

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

ActionName = Literal["navigate", "click", "fill", "wait"]
WaitObservationStatus = Literal["success", "actionable", "normal_timeout", "abnormal_stuck"]
WaitObservationDecisionName = Literal["normal_waiting", "abnormal_stuck", "ready_for_next_action", "task_completed"]
RunStatus = Literal["queued", "running", "succeeded", "failed"]
RunErrorType = Literal["model_error", "system_error"]
ValidationStatus = Literal["running", "succeeded", "failed"]
ReportConclusion = Literal["keep", "optimize", "fix"]


def utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc)


class ApiResponse(BaseModel):
    """统一 API 响应结构。"""

    success: bool = True
    message: str = "ok"
    data: Any | None = None

# ========= Demo require========== #

class Persona(BaseModel):
    """描述当前 run 使用的 persona。"""

    id: str = "persona-default"
    name: str = "默认测试用户"
    description: str = "会按照页面主路径逐步完成任务，不进行高风险操作。"
    skill_level: str = "newbie"  # 用户熟练度，newbie 表示新手型用户。
    patience_level: str = "medium"  # 用户耐心程度，medium 表示遇到小问题会继续尝试。
    risk_preference: str = "low"  # 用户风险偏好，low 表示倾向安全操作，不主动尝试高风险动作。


class Task(BaseModel):
    """描述当前 run 使用的任务。"""

    id: str = "task-default"
    name: str = "完成页面任务"
    description: str = "进入页面后，根据页面提示完成当前任务；如页面要求填写表单，可自行生成合理的测试数据。"
    start_url: str
    success_criteria: list[str] = Field(default_factory=list)
    max_steps: int = 8
    allowed_actions: list[ActionName] = Field(default_factory=lambda: ["navigate", "click", "fill", "wait"])
    risk_level: str = "low"
    destructive_action_allowed: bool = False  # 是否允许执行"破坏性动作":删除/提交/发布/支付等


class RunRequest(BaseModel):
    """定义启动 run 的请求体。"""

    run_name: str = "run"
    headless: bool | None = None  # 是否无头浏览器模式，None系统默认,True不打开浏览器,后台跑, False打开浏览器窗口

# ========= Demo require========== #

class ObservedElement(BaseModel):
    """描述可交互元素摘要。"""

    text: str = ""  # 元素上显示的文本(如按钮文本)
    selector: str = ""  # 元素的 CSS 选择器路径, 定位信息


class FormFieldState(BaseModel):
    """描述表单字段摘要。"""

    name: str = ""
    selector: str = ""
    value: str = ""  # 该字段当前的值(已填)


class ObservedPageState(BaseModel):
    """描述页面观察结果。"""

    current_url: str  # 页面URL
    title: str  # 页面标题
    visible_text_summary: str  # 页面可见文本摘要
    clickable_elements: list[ObservedElement] = Field(default_factory=list)  # 页面上可点击元素列表
    form_fields: list[FormFieldState] = Field(default_factory=list)  # 页面上表单字段列表
    error_messages: list[str] = Field(default_factory=list)  # 页面上检测到的错误信息列表，如表单验证错误、加载失败等
    screenshot_path: str | None = None  # 本次页面观察对应的截图路径


class ActionInput(BaseModel):
    """描述下一步受控动作。"""

    action: ActionName  # "navigate", "click"...
    target: str | None = None  # 动作目标元素；wait 动作允许为空
    value: str | int | None = None  # 动作附带值(非所有动作都需要,例如: fill 需要填内容, wait 可填写毫秒数)
    reason: str = ""  # 执行动作的原因

    @model_validator(mode="after")
    def _normalize_and_validate(self) -> "ActionInput":
        if self.action in {"click", "fill", "navigate"} and not self.target:
            raise ValueError(f"target is required for {self.action} actions.")
        if self.action == "wait" and self.value is None:
            self.value = 300
        if self.action == "fill" and self.value is not None and not isinstance(self.value, str):
            self.value = str(self.value)
        if self.action == "wait" and self.value is not None and not isinstance(self.value, str | int):
            self.value = str(self.value)
        return self


class ExecutionResult(BaseModel):
    """描述动作执行结果。"""

    action: ActionName  # 实际执行动作:click/fill/navagate...
    success: bool  # 是否执行成功?
    detail: str  # 执行结果的文字说明
    error_message: str | None = None  # 执行失败的错误信息


class ValidationResult(BaseModel):
    """描述当前步骤的验证结论。"""  # 描述本次动作的执行结果

    status: ValidationStatus  # 当前验证状态(running/succeded/failed)
    should_stop: bool  # 判断: 是否需要停止
    progress_summary: str  # 本次推进的文字总结
    friction_signals: list[str] = Field(default_factory=list)  # 摩擦信号列表(记录体验问题)
    detected_success: bool = False  # 是否检测到任务成功?
    detected_error: bool = False  # 是否检测到任务失败?


class StepLog(BaseModel):
    """描述单步执行日志。"""  # 记录每步的执行步骤序号/页面观察结果/执行的动作/动作执行的结果/动作的验证结论

    step_index: int  # 步骤编号1/2/3
    observed_page_state: ObservedPageState  # 页面观察结果(页面快照)
    decided_action: ActionInput  # 动作输入(准备做什么)
    execution_result: ExecutionResult  # 动作执行结果
    validation_result: ValidationResult  # 动作验证结果
    post_action_page_state: ObservedPageState  # 动作/等待结束后的页面观察结果
    wait_observation_status: WaitObservationStatus | None = None  # 等待观察节点最终状态
    wait_observation_reason: str | None = None  # 等待观察节点最终判断原因
    wait_observation_observations: int | None = None  # 等待观察节点观察次数
    wait_observation_elapsed_ms: int | None = None  # 等待观察节点累计等待时长
    wait_observation_timeout_ms: int | None = None  # 等待观察节点本次使用的超时上限
    wait_observation_terminal_decision: WaitObservationDecisionName | None = None  # 等待观察节点终止时的模型判断
    wait_observation_traces: list[dict[str, Any]] = Field(default_factory=list)  # 每次等待观察模型判断记录


class RunReport(BaseModel):
    """描述最终 run 报告。"""

    run_id: str  # 单次run的唯一id
    status: RunStatus  # run 的最终状态
    summary: str  # run的文字总结
    success: bool # run 是否成功
    conclusion: ReportConclusion  # 本次 run 的最终结论级别
    persona: Persona  # 使用的是哪个人格
    task: Task  # run 执行的是哪个任务
    total_steps: int  # 总步数
    friction_signals: list[str] = Field(default_factory=list)  # run 中的摩擦信号列表
    key_findings: list[str] = Field(default_factory=list)  # run 的关键发现
    next_recommendations: list[str] = Field(default_factory=list)  # 本次run 的后续建议
    error_type: RunErrorType | None = None  # run 失败时的错误类型
    error_message: str | None = None  # run 失败时的原始错误信息


class RunRecord(BaseModel):
    """描述内存中的运行记录。"""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: RunStatus = "queued"  # run 的运行状态:queued/running/succeeded/failed
    request: RunRequest  # 启动run的请求体内容
    persona: Persona  # 使用的人格
    task: Task  # run 任务
    created_at: datetime = Field(default_factory=utc_now)  # 创建时间
    updated_at: datetime = Field(default_factory=utc_now)  # 更新时间
    error_type: RunErrorType | None = None  # 报错类型
    error_message: str | None = None  # 报错消息


class RunStatusResponse(BaseModel):
    """描述运行状态接口返回值。"""  # 与RunRecord差不多,但是是给前端使用(非内部调用)

    run_id: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    error_type: RunErrorType | None = None
    error_message: str | None = None

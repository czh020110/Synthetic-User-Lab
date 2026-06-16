from __future__ import annotations

# ============================ Run 数据模型模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 定义 run 的请求、页面观察、动作、步骤日志与报告结构
# 模块数据流: API 请求 -> LangGraph 状态 -> 执行结果/报告 -> API 响应
# 模块接口说明: 各 BaseModel 作为模块间统一输入输出结构

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, TypeAlias
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

ActionName: TypeAlias = Literal[
    "navigate", "click", "fill", "wait",
    "press", "scroll", "upload", "select",
    "hover", "check", "uncheck", "dblclick",
    "drag", "ask_for_help", "abandon",
]
WaitObservationStatus: TypeAlias = Literal["success", "actionable", "normal_timeout", "abnormal_stuck"]
WaitObservationDecisionName: TypeAlias = Literal[
    "normal_waiting", "abnormal_stuck", "ready_for_next_action", "task_completed"
]
RunStatus: TypeAlias = Literal["queued", "running", "succeeded", "failed"]
RunErrorType: TypeAlias = Literal["model_error", "system_error"]
ValidationStatus: TypeAlias = Literal["running", "succeeded", "failed"]
ReportConclusion: TypeAlias = Literal["keep", "optimize", "fix"]
FrictionSeverity: TypeAlias = Literal["low", "medium", "high"]
RetrievalSourceType: TypeAlias = Literal["product_knowledge", "failure_case"]


class ClickActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)


class FillActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)


class WaitActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_ms: int = Field(default=1000, ge=0)


class NavigateActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(..., min_length=1)


class PressActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str | None = Field(default=None, min_length=1)
    key: str = Field(..., min_length=1)


class ScrollActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str | None = Field(default=None, min_length=1)
    direction: Literal["up", "down"] = Field(default="down")
    amount: int = Field(default=300, ge=0)


class UploadActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)
    file_paths: list[str] = Field(default_factory=list)
    content: str | None = Field(default=None)
    filename: str = Field(default="test-upload.txt")


class SelectActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)
    values: list[str] = Field(..., min_length=1)


class HoverActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)


class CheckActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)


class UncheckActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)


class DblclickActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selector: str = Field(..., min_length=1)


class DragActionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_selector: str = Field(..., min_length=1)
    end_selector: str = Field(..., min_length=1)


class AskForHelpPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1)


class AbandonPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(..., min_length=1)


ActionPayload: TypeAlias = (
    ClickActionPayload | FillActionPayload | WaitActionPayload | NavigateActionPayload
    | PressActionPayload | ScrollActionPayload | UploadActionPayload | SelectActionPayload
    | HoverActionPayload | CheckActionPayload | UncheckActionPayload | DblclickActionPayload
    | DragActionPayload | AskForHelpPayload | AbandonPayload
)


@dataclass(frozen=True)
class ActionDefinition:
    name: ActionName
    description: str
    payload_model: type[ActionPayload]
    payload_description: str


ACTION_REGISTRY: dict[ActionName, ActionDefinition] = {
    "navigate": ActionDefinition(
        name="navigate",
        description="跳转到任务允许的 URL。",
        payload_model=NavigateActionPayload,
        payload_description='payload 必须为 {"url": "目标 URL"}',
    ),
    "click": ActionDefinition(
        name="click",
        description="点击页面上已经观察到的可点击元素。",
        payload_model=ClickActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器"}',
    ),
    "fill": ActionDefinition(
        name="fill",
        description="填写页面上已经观察到的表单字段。",
        payload_model=FillActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器", "value": "填写内容"}',
    ),
    "wait": ActionDefinition(
        name="wait",
        description="等待页面状态变化。",
        payload_model=WaitActionPayload,
        payload_description='payload 必须为 {"duration_ms": 等待毫秒数}，没有明确时使用 1000',
    ),
    "press": ActionDefinition(
        name="press",
        description="按下键盘按键，如 Enter 提交、Tab 切换焦点、Escape 关闭弹窗。",
        payload_model=PressActionPayload,
        payload_description='payload 必须为 {"key": "按键名", "selector": "目标元素选择器(可选)"}，有 selector 时先 focus 到元素再按键',
    ),
    "scroll": ActionDefinition(
        name="scroll",
        description="在页面上滚动以查看更多内容。",
        payload_model=ScrollActionPayload,
        payload_description='payload 必须为 {"selector": "元素选择器(可选)", "direction": "up 或 down", "amount": 像素数}，有 selector 时滚元素内部，无则滚页面',
    ),
    "upload": ActionDefinition(
        name="upload",
        description="上传文件到页面的文件输入框。",
        payload_model=UploadActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器", "file_paths": ["文件路径"]} 或 {"selector": "CSS 选择器", "content": "文件内容", "filename": "文件名(可选)"}',
    ),
    "select": ActionDefinition(
        name="select",
        description="在下拉框中选择选项。",
        payload_model=SelectActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器", "values": ["选项值"]}',
    ),
    "hover": ActionDefinition(
        name="hover",
        description="鼠标悬停在元素上以触发菜单、提示或子菜单。",
        payload_model=HoverActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器"}',
    ),
    "check": ActionDefinition(
        name="check",
        description="勾选复选框或单选按钮。",
        payload_model=CheckActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器"}',
    ),
    "uncheck": ActionDefinition(
        name="uncheck",
        description="取消勾选复选框。",
        payload_model=UncheckActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器"}',
    ),
    "dblclick": ActionDefinition(
        name="dblclick",
        description="双击元素。",
        payload_model=DblclickActionPayload,
        payload_description='payload 必须为 {"selector": "CSS 选择器"}',
    ),
    "drag": ActionDefinition(
        name="drag",
        description="将元素从起点拖拽到终点。",
        payload_model=DragActionPayload,
        payload_description='payload 必须为 {"start_selector": "起点 CSS 选择器", "end_selector": "终点 CSS 选择器"}',
    ),
    "ask_for_help": ActionDefinition(
        name="ask_for_help",
        description="用户卡住时请求帮助，表示当前流程无法继续。执行后 run 将以需要帮助状态终止。",
        payload_model=AskForHelpPayload,
        payload_description='payload 必须为 {"message": "求助说明"}',
    ),
    "abandon": ActionDefinition(
        name="abandon",
        description="用户放弃当前任务。执行后 run 将以放弃状态终止。",
        payload_model=AbandonPayload,
        payload_description='payload 必须为 {"reason": "放弃原因"}',
    ),
}


def render_action_definitions() -> str:
    return "\n".join(
        f"- {definition.name}：{definition.description}{definition.payload_description}。"
        for definition in ACTION_REGISTRY.values()
    )


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


class RetrievedContextItem(BaseModel):
    """描述检索到的上下文片段。"""

    source_type: RetrievalSourceType
    title: str
    content: str
    source_ref: str = ""


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

    model_config = ConfigDict(extra="forbid")

    action: ActionName = Field(description="动作名称，必须是可选动作之一")
    payload: Any = Field(description="动作参数对象，字段取决于 action 类型，不要用 target/value 等其他字段名")
    reason: str = Field(default="", description="一句中文说明选择该动作的原因")

    @model_validator(mode="after")
    def _normalize_and_validate(self) -> "ActionInput":
        definition = ACTION_REGISTRY[self.action]
        if isinstance(self.payload, dict):
            self.payload = definition.payload_model.model_validate(self.payload)
        elif not isinstance(self.payload, definition.payload_model):
            self.payload = definition.payload_model.model_validate(self.payload.model_dump())
        return self


class ExecutionResult(BaseModel):
    """描述动作执行结果。"""

    action: ActionName  # 实际执行动作:click/fill/navagate...
    success: bool  # 是否执行成功?
    detail: str  # 执行结果的文字说明
    error_message: str | None = None  # 执行失败的错误信息


class ValidationResult(BaseModel):
    """描述当前步骤的验证结论。"""

    status: ValidationStatus = Field(description="当前验证状态: running/succeeded/failed")
    should_stop: bool = Field(description="是否需要停止运行")
    progress_summary: str = Field(description="本次推进的文字总结")
    friction_signals: list[str] = Field(default_factory=list, description="摩擦信号列表，记录体验问题")
    detected_success: bool = Field(default=False, description="是否检测到任务成功")
    detected_error: bool = Field(default=False, description="是否检测到任务失败")


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
    retrieval_context: list[RetrievedContextItem] = Field(default_factory=list)  # 检索到的上下文片段

    @computed_field
    @property
    def before_page_state(self) -> ObservedPageState:
        return self.observed_page_state

    @computed_field
    @property
    def after_page_state(self) -> ObservedPageState:
        return self.post_action_page_state


class FrictionIssue(BaseModel):
    """描述一个结构化摩擦问题。"""

    signal: str  # 摩擦信号类型标识符
    severity: FrictionSeverity  # 严重程度
    step_indexes: list[int]  # 受影响的步骤编号列表
    description: str  # 人类可读的问题描述
    suggested_fix: str = ""  # 可选的修复建议


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
    friction_issues: list[FrictionIssue] = Field(default_factory=list)  # 结构化摩擦问题列表
    key_findings: list[str] = Field(default_factory=list)  # run 的关键发现
    next_recommendations: list[str] = Field(default_factory=list)  # 本次run 的后续建议
    step_details: list[dict[str, Any]] = Field(default_factory=list)  # 报告中的结构化步骤明细
    structured_facts: dict[str, Any] | None = Field(default=None, description="代码提取的结构化事实摘要，供前端展示或二次分析")
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

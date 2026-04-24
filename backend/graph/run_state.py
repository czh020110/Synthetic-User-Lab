from __future__ import annotations

# ============================ LangGraph 状态模块 ============================ #
# 使用技术栈: Python / TypedDict
# 模块功能: 定义 demo run 在图内共享的状态字段
# 模块数据流: API 输入 -> GraphState -> 各节点增量更新 -> 最终报告
# 模块接口说明: DemoRunState 作为 StateGraph 的状态 schema

from pathlib import Path
from typing import Any

from typing_extensions import NotRequired, Required, TypedDict

from backend.schemas.run_schemas import (
    ActionInput,
    DemoPersona,
    DemoTask,
    ExecutionResult,
    ObservedPageState,
    RunRecord,
    RunRequest,
    RunReport,
    StepLog,
    ValidationResult,
)

# 主Graph状态
class DemoRunState(TypedDict):  # 目前是demo
    run_id: Required[str]
    request: Required[RunRequest]
    screenshot_dir: Required[Path]
    app_base_url: Required[str]
    record: NotRequired[RunRecord]  # 目前是demo 
    persona: NotRequired[DemoPersona]  # 目前是demo
    task: NotRequired[DemoTask]  # 目前是demo
    session: NotRequired[dict[str, Any]]
    current_page_state: NotRequired[ObservedPageState]
    current_action: NotRequired[ActionInput]
    current_execution_result: NotRequired[ExecutionResult]
    current_validation_result: NotRequired[ValidationResult]
    step_logs: NotRequired[list[StepLog]]
    current_step_index: NotRequired[int]
    should_stop: NotRequired[bool]
    report: NotRequired[RunReport]

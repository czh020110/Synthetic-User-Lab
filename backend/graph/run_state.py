from __future__ import annotations

# ============================ LangGraph 状态模块 ============================ #
# 使用技术栈: Python / TypedDict
# 模块功能: 定义 run 在图内共享的状态字段
# 模块数据流: API 输入 -> GraphState -> 各节点增量更新 -> 最终报告
# 模块接口说明: RunState 作为 StateGraph 的状态 schema

from pathlib import Path
from typing import Any

from typing_extensions import NotRequired, Required, TypedDict

from backend.schemas.run_schemas import (
    ActionInput,
    ExecutionResult,
    ObservedPageState,
    Persona,
    RunRecord,
    RunRequest,
    RunReport,
    StepLog,
    Task,
    ValidationResult,
    WaitObservationDecisionName,
    WaitObservationStatus,
)

# 主Graph状态
class RunState(TypedDict):
    run_id: Required[str]
    request: Required[RunRequest]
    screenshot_dir: Required[Path]
    app_base_url: Required[str]
    record: NotRequired[RunRecord]
    persona: NotRequired[Persona]
    task: NotRequired[Task]
    session: NotRequired[dict[str, Any]]
    current_page_state: NotRequired[ObservedPageState]
    step_before_page_state: NotRequired[ObservedPageState]
    post_action_page_state: NotRequired[ObservedPageState]
    session_box: NotRequired[dict[str, Any]]
    current_action: NotRequired[ActionInput]
    current_execution_result: NotRequired[ExecutionResult]
    current_validation_result: NotRequired[ValidationResult]
    step_logs: NotRequired[list[StepLog]]
    current_step_index: NotRequired[int]
    should_stop: NotRequired[bool]
    wait_observation_status: NotRequired[WaitObservationStatus | None]
    wait_observation_reason: NotRequired[str | None]
    wait_observation_observations: NotRequired[int | None]
    wait_observation_elapsed_ms: NotRequired[int | None]
    wait_observation_timeout_ms: NotRequired[int | None]
    wait_observation_terminal_decision: NotRequired[WaitObservationDecisionName | None]
    wait_observation_traces: NotRequired[list[dict[str, Any]] | None]
    wait_observation_round: NotRequired[int | None]
    wait_agent: NotRequired[Any]
    decide_agent: NotRequired[Any]
    validate_agent: NotRequired[Any]
    report: NotRequired[RunReport]

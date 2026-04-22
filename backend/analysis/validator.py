from __future__ import annotations

# ============================ 验证模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 根据页面状态、执行结果和步数判断是否成功、失败或继续
# 模块数据流: ObservedPageState + ExecutionResult + StepLog -> ValidationResult
# 模块接口说明: validate_progress() 返回当前步骤验证结果

from backend.schemas.run_schemas import DemoTask, ExecutionResult, ObservedPageState, StepLog, ValidationResult


def validate_progress(
    task: DemoTask,
    observed_page_state: ObservedPageState,
    execution_result: ExecutionResult,
    previous_steps: list[StepLog],
    current_step_index: int,
) -> ValidationResult:
    """根据最小规则判断当前运行状态。"""

    friction_signals: list[str] = []

    if not execution_result.success:
        friction_signals.append("action_failed")
        return ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary=execution_result.error_message or "动作执行失败。",
            friction_signals=friction_signals,
            detected_error=True,
        )

    if task.success_text in observed_page_state.visible_text_summary:
        return ValidationResult(
            status="succeeded",
            should_stop=True,
            progress_summary="页面已出现成功文案，任务完成。",
            detected_success=True,
        )

    if observed_page_state.error_messages:
        friction_signals.append("page_error")
        return ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary="页面出现错误提示，结束本次运行。",
            friction_signals=friction_signals,
            detected_error=True,
        )

    if current_step_index >= task.max_steps:
        friction_signals.append("step_limit_reached")
        return ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary="超过最大步数限制，结束本次运行。",
            friction_signals=friction_signals,
            detected_error=True,
        )

    if previous_steps:
        last_action = previous_steps[-1].decided_action
        if last_action.action == "wait" and execution_result.action == "wait":
            friction_signals.append("repeated_wait")

    return ValidationResult(
        status="running",
        should_stop=False,
        progress_summary="任务仍在进行，继续执行下一步。",
        friction_signals=friction_signals,
    )

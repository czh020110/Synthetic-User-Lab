from __future__ import annotations

from urllib.parse import urlsplit

from backend.schemas.run_schemas import (
    ActionInput,
    ExecutionResult,
    ObservedPageState,
    StepLog,
    Task,
    ValidationResult,
)


def validate_progress(
    task: Task,
    observed_page_state: ObservedPageState,
    execution_result: ExecutionResult,
    previous_steps: list[StepLog],
    current_step_index: int,
    current_action: ActionInput | None = None,
    agent_validation: ValidationResult | None = None,
) -> ValidationResult:
    """综合执行结果、页面事实、agent 判断和历史步骤，输出当前步骤的最终验证结论。"""

    if not execution_result.success:
        return ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary=execution_result.error_message or "动作执行失败。",
            friction_signals=["action_failed"],
            detected_error=True,
        )

    if observed_page_state.error_messages:
        return ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary="页面出现错误提示，结束本次运行。",
            friction_signals=["page_error"],
            detected_error=True,
        )

    base_result = _normalize_agent_validation(agent_validation)

    if base_result.status == "succeeded":
        return base_result.model_copy(
            update={
                "friction_signals": _dedupe_signals(base_result.friction_signals),
                "progress_summary": base_result.progress_summary or "任务已完成。",
                "detected_success": True,
                "detected_error": False,
                "should_stop": True,
            }
        )

    if current_step_index >= task.max_steps:
        return ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary="超过最大步数限制，结束本次运行。",
            friction_signals=["step_limit_reached"],
            detected_error=True,
        )

    wait_streak = _count_consecutive_waits(previous_steps, current_action)
    repeated_action_streak = _count_consecutive_action_target(previous_steps, current_action)
    stable_page_streak = _count_stable_page_streak(previous_steps, observed_page_state)
    off_track_streak = _count_off_track_streak(task, previous_steps, current_action, observed_page_state)
    should_defer_to_wait_observer = stable_page_streak >= 3 and _action_can_stall(current_action)

    friction_signals = list(base_result.friction_signals)
    recovery_reasons: list[str] = []

    if wait_streak >= 3:
        friction_signals.append("repeated_wait")
        if wait_streak >= 4 and not should_defer_to_wait_observer:
            return _failed_result(
                friction_signals,
                "连续等待多次仍无进展，结束本次运行。",
            )
        recovery_reasons.append("连续等待仍无进展，可考虑恢复路径。")

    if repeated_action_streak >= 3:
        friction_signals.append("repeated_action_target")
        if repeated_action_streak >= 4 and not should_defer_to_wait_observer:
            return _failed_result(
                friction_signals,
                "同一动作重复执行仍无进展，结束本次运行。",
            )
        recovery_reasons.append("同一动作重复执行仍无进展，可考虑恢复路径。")

    if stable_page_streak >= 3 and _action_can_stall(current_action):
        friction_signals.append("stuck_page")
        recovery_reasons.append("页面连续多步没有变化，进入等待观察以确认是否仍在处理。")

    if off_track_streak >= 3:
        friction_signals.append("off_track_navigation")
        if off_track_streak >= 4 and not should_defer_to_wait_observer:
            return _failed_result(
                friction_signals,
                "连续多步跳转或等待后仍偏离任务主路径，结束本次运行。",
            )
        recovery_reasons.append("当前路径可能已偏离任务目标，可考虑恢复路径。")

    if recovery_reasons:
        friction_signals.append("recovery_candidate")

    progress_summary = base_result.progress_summary
    if recovery_reasons and base_result.status == "running":
        progress_summary = recovery_reasons[0]
    elif not progress_summary:
        progress_summary = "任务仍在进行，继续执行下一步。"

    return base_result.model_copy(
        update={
            "friction_signals": _dedupe_signals(friction_signals),
            "progress_summary": progress_summary,
        }
    )


def _normalize_agent_validation(agent_validation: ValidationResult | None) -> ValidationResult:
    """将 agent 验证结果收敛为规则层可继续处理的基础验证结论。"""

    if agent_validation is None:
        return ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="任务仍在进行，继续执行下一步。",
        )

    if agent_validation.status == "succeeded":
        return ValidationResult(
            status="succeeded",
            should_stop=True,
            progress_summary=agent_validation.progress_summary or "任务已完成。",
            friction_signals=agent_validation.friction_signals,
            detected_success=True,
            detected_error=False,
        )

    if agent_validation.status == "failed" and not agent_validation.detected_error:
        return ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="尚未出现可确认的失败条件，继续观察后续步骤。",
            friction_signals=agent_validation.friction_signals,
        )

    return agent_validation.model_copy(deep=True)


def _failed_result(friction_signals: list[str], progress_summary: str) -> ValidationResult:
    """根据摩擦信号和失败摘要构造统一的失败验证结果。"""

    return ValidationResult(
        status="failed",
        should_stop=True,
        progress_summary=progress_summary,
        friction_signals=_dedupe_signals(friction_signals),
        detected_error=True,
    )


def _count_consecutive_waits(previous_steps: list[StepLog], current_action: ActionInput | None) -> int:
    """统计当前动作之前连续执行 wait 的步数。"""

    if current_action is None or current_action.action != "wait":
        return 0

    streak = 1
    for step in reversed(previous_steps):
        if step.decided_action.action != "wait":
            break
        streak += 1
    return streak


def _count_consecutive_action_target(previous_steps: list[StepLog], current_action: ActionInput | None) -> int:
    """统计连续执行相同 click 或 navigate 目标的步数。"""

    if current_action is None or current_action.action not in {"click", "navigate"}:
        return 0

    streak = 1
    current_signature = (current_action.action, current_action.payload.model_dump(mode="json"))
    for step in reversed(previous_steps):
        previous_signature = (step.decided_action.action, step.decided_action.payload.model_dump(mode="json"))
        if previous_signature != current_signature:
            break
        streak += 1
    return streak


def _count_stable_page_streak(previous_steps: list[StepLog], observed_page_state: ObservedPageState) -> int:
    """统计页面 URL 和可见文本摘要连续保持不变的步数。"""

    streak = 1
    current_fingerprint = _page_fingerprint(observed_page_state)
    for step in reversed(previous_steps):
        if _page_fingerprint(step.observed_page_state) != current_fingerprint:
            break
        streak += 1
    return streak


def _count_off_track_streak(
    task: Task,
    previous_steps: list[StepLog],
    current_action: ActionInput | None,
    observed_page_state: ObservedPageState,
) -> int:
    """统计连续在非任务起始页执行 navigate 或 wait 的偏航步数。"""

    if current_action is None or current_action.action not in {"navigate", "wait"}:
        return 0

    if _is_task_start_page(task.start_url, observed_page_state.current_url):
        return 0

    streak = 1
    for step in reversed(previous_steps):
        if step.decided_action.action not in {"navigate", "wait"}:
            break
        if _is_task_start_page(task.start_url, step.observed_page_state.current_url):
            break
        streak += 1
    return streak


def _is_task_start_page(start_url: str, current_url: str) -> bool:
    """判断当前页面是否与任务起始 URL 属于同一页面路径。"""

    start_parts = urlsplit(start_url)
    current_parts = urlsplit(current_url)
    return (
        start_parts.scheme == current_parts.scheme
        and start_parts.netloc == current_parts.netloc
        and start_parts.path == current_parts.path
    )


def _action_can_stall(current_action: ActionInput | None) -> bool:
    """判断当前动作是否适合参与页面停滞判定。"""

    return current_action is None or current_action.action != "fill"


def _page_fingerprint(page_state: ObservedPageState) -> tuple[str, str]:
    """生成用于判断页面是否变化的轻量页面指纹。"""

    return page_state.current_url, " ".join(page_state.visible_text_summary.split())


def _dedupe_signals(friction_signals: list[str]) -> list[str]:
    """按原始顺序去除重复和空的摩擦信号。"""

    deduped: list[str] = []
    for signal in friction_signals:
        if signal and signal not in deduped:
            deduped.append(signal)
    return deduped

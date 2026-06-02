from __future__ import annotations

from backend.retrieval.failure_recovery import (
    choose_recovery_action,
    retrieve_failure_cases,
    _build_failure_query,
)
from backend.schemas.run_schemas import (
    ActionInput,
    ExecutionResult,
    NavigateActionPayload,
    ObservedPageState,
    PressActionPayload,
    RetrievedContextItem,
    StepLog,
    Task,
    ValidationResult,
)


def _make_task(start_url: str = "https://example.com") -> Task:
    return Task(
        name="test-task",
        description="test task",
        start_url=start_url,
        success_criteria=["task done"],
        max_steps=10,
        allowed_actions=["click", "fill", "navigate", "press", "wait", "abandon"],
        risk_level="low",
    )


def _make_step_log(
    error_message: str | None = None,
    progress_summary: str | None = None,
) -> StepLog:
    page = ObservedPageState(current_url="https://example.com", title="Test", visible_text_summary="test page")
    action = ActionInput(action="navigate", payload=NavigateActionPayload(url="https://example.com"), reason="test")
    exec_result = ExecutionResult(
        action="navigate",
        success=True,
        detail="ok",
        error_message=error_message,
    )
    val_result = ValidationResult(
        status="running",
        should_stop=False,
        progress_summary=progress_summary or "in progress",
    )
    return StepLog(
        step_index=1,
        observed_page_state=page,
        decided_action=action,
        execution_result=exec_result,
        validation_result=val_result,
        post_action_page_state=page,
    )


class TestRetrieveFailureCases:
    def test_empty_friction_signals_returns_empty(self):
        result = retrieve_failure_cases([], [])
        assert result == []

    def test_exact_pattern_match(self):
        result = retrieve_failure_cases(["repeated_action_target"], [])
        assert len(result) >= 1
        assert result[0].title == "失败案例: 同一动作重复执行多次仍无进展"
        assert "navigate" in result[0].content

    def test_keyword_match(self):
        step = _make_step_log(error_message="重复点击无效")
        result = retrieve_failure_cases(["unknown_signal"], [step])
        assert len(result) >= 1
        assert any("重复" in item.content for item in result)

    def test_multiple_signals_ranked_by_score(self):
        result = retrieve_failure_cases(["repeated_action_target", "page_error"], [])
        assert len(result) >= 2

    def test_returns_retrieved_context_items(self):
        result = retrieve_failure_cases(["stuck_page"], [])
        for item in result:
            assert isinstance(item, RetrievedContextItem)
            assert item.source_type == "failure_case"


class TestChooseRecoveryAction:
    def test_navigate_recovery_for_stuck_page(self):
        task = _make_task()
        action = choose_recovery_action(
            task=task,
            friction_signals=["stuck_page"],
            step_logs=[],
            recovery_history=[],
        )
        assert action.action == "navigate"
        assert isinstance(action.payload, NavigateActionPayload)
        assert action.payload.url == "https://example.com"

    def test_press_recovery_for_page_error(self):
        task = _make_task()
        action = choose_recovery_action(
            task=task,
            friction_signals=["page_error"],
            step_logs=[],
            recovery_history=[],
        )
        assert action.action == "press"
        assert isinstance(action.payload, PressActionPayload)
        assert action.payload.key == "Escape"

    def test_avoids_repeated_pattern_and_falls_through(self):
        task = _make_task()
        history = [{"error_pattern": "repeated_action_target", "action": "navigate", "reason": "recovery"}]
        step = _make_step_log(error_message="页面出现错误弹窗")
        action = choose_recovery_action(
            task=task,
            friction_signals=["repeated_action_target"],
            step_logs=[step],
            recovery_history=history,
        )
        assert action.action == "press"

    def test_single_pattern_tried_abandons_when_no_alternative(self):
        task = _make_task()
        history = [{"error_pattern": "stuck_page", "action": "navigate", "reason": "recovery"}]
        action = choose_recovery_action(
            task=task,
            friction_signals=["stuck_page"],
            step_logs=[],
            recovery_history=history,
        )
        assert action.action == "abandon"

    def test_fallback_navigate_when_no_pattern_matched(self):
        task = _make_task()
        action = choose_recovery_action(
            task=task,
            friction_signals=["unheard_signal_xyz"],
            step_logs=[],
            recovery_history=[],
        )
        assert action.action == "navigate"

    def test_abandon_when_all_exhausted(self):
        task = _make_task()
        history = [
            {"error_pattern": "stuck_page", "action": "navigate", "reason": "r"},
            {"error_pattern": "page_error", "action": "press", "reason": "r"},
            {"error_pattern": "repeated_action_target", "action": "navigate", "reason": "r"},
            {"error_pattern": "off_track_navigation", "action": "navigate", "reason": "r"},
            {"error_pattern": "repeated_wait", "action": "click", "reason": "r"},
        ]
        action = choose_recovery_action(
            task=task,
            friction_signals=["stuck_page"],
            step_logs=[],
            recovery_history=history,
        )
        assert action.action == "abandon"

    def test_with_step_logs_informs_decision(self):
        task = _make_task()
        step = _make_step_log(error_message="超时等待", progress_summary="无进展")
        action = choose_recovery_action(
            task=task,
            friction_signals=["repeated_wait"],
            step_logs=[step],
            recovery_history=[],
        )
        assert action.action in ("navigate", "click")


class TestBuildFailureQuery:
    def test_combines_signals_and_step_info(self):
        step = _make_step_log(error_message="ERR", progress_summary="no progress")
        query = _build_failure_query(["stuck_page"], [step])
        assert "stuck_page" in query
        assert "err" in query
        assert "no progress" in query

    def test_empty_logs_only_signals(self):
        query = _build_failure_query(["page_error"], [])
        assert "page_error" in query

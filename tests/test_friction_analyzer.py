from __future__ import annotations

from typing import cast

from backend.analysis.friction_analyzer import analyze_friction
from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    ClickActionPayload,
    ExecutionResult,
    FillActionPayload,
    NavigateActionPayload,
    ObservedPageState,
    StepLog,
    ValidationResult,
    ValidationStatus,
)

START_URL = "http://127.0.0.1:8765/demo/index.html"
FORM_URL = "http://127.0.0.1:8765/demo/form.html"
DASHBOARD_URL = "http://127.0.0.1:8765/dashboard"


def make_page_state(
    *,
    url: str = START_URL,
    title: str = "demo",
    visible_text_summary: str = "页面内容",
    error_messages: list[str] | None = None,
) -> ObservedPageState:
    return ObservedPageState(
        current_url=url,
        title=title,
        visible_text_summary=visible_text_summary,
        clickable_elements=[],
        form_fields=[],
        error_messages=error_messages or [],
    )


def make_click_step(
    *,
    step_index: int = 1,
    selector: str = "#submit",
    url: str = START_URL,
    after_url: str | None = None,
    visible_text_summary: str = "页面内容",
    after_text: str = "页面内容",
    execution_success: bool = True,
    validation_status: ValidationStatus = "running",
    friction_signals: list[str] | None = None,
    after_error_messages: list[str] | None = None,
    detected_success: bool = False,
) -> StepLog:
    return StepLog(
        step_index=step_index,
        observed_page_state=make_page_state(url=url, visible_text_summary=visible_text_summary),
        decided_action=ActionInput(action="click", payload=ClickActionPayload(selector=selector), reason="test"),
        execution_result=ExecutionResult(
            action="click",
            success=execution_success,
            detail="ok" if execution_success else "failed",
            error_message=None if execution_success else "执行失败",
        ),
        validation_result=ValidationResult(
            status=cast(ValidationStatus, validation_status),
            should_stop=validation_status != "running",
            progress_summary="继续",
            friction_signals=friction_signals or [],
            detected_success=detected_success,
        ),
        post_action_page_state=make_page_state(url=after_url or url, visible_text_summary=after_text, error_messages=after_error_messages),
    )


def make_navigate_step(
    *,
    step_index: int = 1,
    from_url: str = START_URL,
    to_url: str = FORM_URL,
    execution_success: bool = True,
    friction_signals: list[str] | None = None,
) -> StepLog:
    return StepLog(
        step_index=step_index,
        observed_page_state=make_page_state(url=from_url),
        decided_action=ActionInput(action="navigate", payload=NavigateActionPayload(url=to_url), reason="test"),
        execution_result=ExecutionResult(
            action="navigate",
            success=execution_success,
            detail="ok" if execution_success else "failed",
        ),
        validation_result=ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="继续",
            friction_signals=friction_signals or [],
        ),
        post_action_page_state=make_page_state(url=to_url),
    )


def make_fill_step(
    *,
    step_index: int = 1,
    url: str = START_URL,
    selector: str = "#name",
    value: str = "test",
    friction_signals: list[str] | None = None,
) -> StepLog:
    return StepLog(
        step_index=step_index,
        observed_page_state=make_page_state(url=url),
        decided_action=ActionInput(action="fill", payload=FillActionPayload(selector=selector, value=value), reason="test"),
        execution_result=ExecutionResult(action="fill", success=True, detail="ok"),
        validation_result=ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="继续",
            friction_signals=friction_signals or [],
        ),
        post_action_page_state=make_page_state(url=url),
    )


# ============================ 空步骤 ============================ #


class TestEmptySteps:
    def test_empty_steps_returns_empty(self):
        assert analyze_friction([]) == []


# ============================ 无摩擦 ============================ #


class TestNoFriction:
    def test_clean_run_no_issues(self):
        steps = [
            make_click_step(step_index=1, selector="#a", visible_text_summary="初始页面", after_text="表单加载"),
            make_fill_step(step_index=2, url=START_URL),
            make_click_step(step_index=3, selector="#b", visible_text_summary="表单已填写", after_text="提交成功"),
        ]
        issues = analyze_friction(steps)
        assert issues == []


# ============================ 重复点击 ============================ #


class TestRepeatedClicks:
    def test_three_clicks_same_selector(self):
        steps = [
            make_click_step(step_index=1, selector="#submit"),
            make_click_step(step_index=2, selector="#submit"),
            make_click_step(step_index=3, selector="#submit"),
        ]
        issues = analyze_friction(steps)
        click_issues = [i for i in issues if i.signal == "repeated_click"]
        assert len(click_issues) == 1
        assert click_issues[0].severity == "medium"
        assert click_issues[0].step_indexes == [1, 2, 3]
        assert "#submit" in click_issues[0].description

    def test_five_clicks_high_severity(self):
        steps = [make_click_step(step_index=i, selector="#btn") for i in range(1, 6)]
        issues = analyze_friction(steps)
        click_issues = [i for i in issues if i.signal == "repeated_click"]
        assert len(click_issues) == 1
        assert click_issues[0].severity == "high"
        assert click_issues[0].step_indexes == [1, 2, 3, 4, 5]

    def test_two_clicks_no_issue(self):
        steps = [
            make_click_step(step_index=1, selector="#submit"),
            make_click_step(step_index=2, selector="#submit"),
        ]
        issues = analyze_friction(steps)
        click_issues = [i for i in issues if i.signal == "repeated_click"]
        assert click_issues == []

    def test_different_selectors_no_issue(self):
        steps = [
            make_click_step(step_index=1, selector="#a"),
            make_click_step(step_index=2, selector="#b"),
            make_click_step(step_index=3, selector="#a"),
        ]
        issues = analyze_friction(steps)
        click_issues = [i for i in issues if i.signal == "repeated_click"]
        assert click_issues == []


# ============================ 返回导航 ============================ #


class TestBackNavigation:
    def test_navigate_back_to_visited_url(self):
        steps = [
            make_navigate_step(step_index=1, from_url=START_URL, to_url=FORM_URL),
            make_navigate_step(step_index=2, from_url=FORM_URL, to_url=DASHBOARD_URL),
            make_navigate_step(step_index=3, from_url=DASHBOARD_URL, to_url=START_URL),
        ]
        issues = analyze_friction(steps)
        back_issues = [i for i in issues if i.signal == "back_navigation"]
        assert len(back_issues) == 1
        assert back_issues[0].severity == "low"
        assert 3 in back_issues[0].step_indexes

    def test_multiple_back_navigations_medium(self):
        steps = [
            make_navigate_step(step_index=1, from_url=START_URL, to_url=FORM_URL),
            make_navigate_step(step_index=2, from_url=FORM_URL, to_url=START_URL),
            make_navigate_step(step_index=3, from_url=START_URL, to_url=FORM_URL),
            make_navigate_step(step_index=4, from_url=FORM_URL, to_url=START_URL),
        ]
        issues = analyze_friction(steps)
        back_issues = [i for i in issues if i.signal == "back_navigation"]
        assert len(back_issues) == 1
        assert back_issues[0].severity == "medium"

    def test_no_back_navigation(self):
        steps = [
            make_navigate_step(step_index=1, from_url=START_URL, to_url=FORM_URL),
            make_navigate_step(step_index=2, from_url=FORM_URL, to_url=DASHBOARD_URL),
        ]
        issues = analyze_friction(steps)
        back_issues = [i for i in issues if i.signal == "back_navigation"]
        assert back_issues == []

    def test_no_duplicate_url_in_seen_urls(self):
        """验证非 navigate 步骤不会重复追加 URL 到 seen_urls。"""
        steps = [
            make_click_step(step_index=1, url=START_URL, after_url=START_URL),
            make_click_step(step_index=2, url=START_URL, after_url=START_URL),
            make_navigate_step(step_index=3, from_url=START_URL, to_url=FORM_URL),
            make_navigate_step(step_index=4, from_url=FORM_URL, to_url=START_URL),
        ]
        issues = analyze_friction(steps)
        back_issues = [i for i in issues if i.signal == "back_navigation"]
        assert len(back_issues) == 1
        assert 4 in back_issues[0].step_indexes

    def test_single_step_navigate_back_detected(self):
        """验证单步 navigate 回初始 URL 能被检测（边缘情况）。"""
        steps = [
            make_navigate_step(step_index=1, from_url=START_URL, to_url=START_URL),
        ]
        issues = analyze_friction(steps)
        back_issues = [i for i in issues if i.signal == "back_navigation"]
        assert len(back_issues) == 1
        assert 1 in back_issues[0].step_indexes


# ============================ 错误恢复 ============================ #


class TestErrorRecovery:
    def test_action_failed_signal(self):
        steps = [
            make_click_step(step_index=1, execution_success=True),
            make_click_step(step_index=2, execution_success=False, friction_signals=["action_failed"]),
        ]
        issues = analyze_friction(steps)
        error_issues = [i for i in issues if i.signal == "error_recovery"]
        assert len(error_issues) == 1
        assert error_issues[0].severity == "high"
        assert 2 in error_issues[0].step_indexes

    def test_page_error_signal(self):
        steps = [
            make_click_step(step_index=1, friction_signals=["page_error"]),
        ]
        issues = analyze_friction(steps)
        error_issues = [i for i in issues if i.signal == "error_recovery"]
        assert len(error_issues) == 1
        assert error_issues[0].severity == "high"

    def test_recovery_candidate_signal(self):
        steps = [
            make_click_step(step_index=1, friction_signals=["recovery_candidate"]),
        ]
        issues = analyze_friction(steps)
        error_issues = [i for i in issues if i.signal == "error_recovery"]
        assert len(error_issues) == 1

    def test_no_error_signals(self):
        steps = [
            make_click_step(step_index=1, execution_success=True),
        ]
        issues = analyze_friction(steps)
        error_issues = [i for i in issues if i.signal == "error_recovery"]
        assert error_issues == []


# ============================ 页面停留 ============================ #


class TestPageDwell:
    def test_three_steps_same_url(self):
        steps = [
            make_click_step(step_index=1, url=START_URL, after_url=START_URL),
            make_fill_step(step_index=2, url=START_URL),
            make_click_step(step_index=3, url=START_URL, after_url=START_URL),
        ]
        issues = analyze_friction(steps)
        dwell_issues = [i for i in issues if i.signal == "page_dwell"]
        assert len(dwell_issues) == 1
        assert dwell_issues[0].severity == "medium"
        assert dwell_issues[0].step_indexes == [1, 2, 3]

    def test_five_steps_high_severity(self):
        steps = [
            make_click_step(step_index=i, url=START_URL, after_url=START_URL)
            for i in range(1, 6)
        ]
        issues = analyze_friction(steps)
        dwell_issues = [i for i in issues if i.signal == "page_dwell"]
        assert len(dwell_issues) == 1
        assert dwell_issues[0].severity == "high"

    def test_url_change_no_dwell(self):
        steps = [
            make_click_step(step_index=1, url=START_URL, after_url=START_URL),
            make_click_step(step_index=2, url=FORM_URL, after_url=FORM_URL),
        ]
        issues = analyze_friction(steps)
        dwell_issues = [i for i in issues if i.signal == "page_dwell"]
        assert dwell_issues == []

    def test_success_stops_dwell_group(self):
        steps = [
            make_click_step(step_index=1, url=START_URL, after_url=START_URL, visible_text_summary="内容", after_text="内容"),
            make_click_step(step_index=2, url=START_URL, after_url=START_URL, visible_text_summary="内容", after_text="内容", validation_status="succeeded", detected_success=True),
            make_click_step(step_index=3, url=START_URL, after_url=START_URL, visible_text_summary="内容", after_text="内容"),
        ]
        issues = analyze_friction(steps)
        dwell_issues = [i for i in issues if i.signal == "page_dwell"]
        assert dwell_issues == []


# ============================ 迷失导航 ============================ #


class TestLostNavigation:
    def test_off_track_signal(self):
        steps = [
            make_navigate_step(step_index=1, from_url=START_URL, to_url=FORM_URL, friction_signals=["off_track_navigation"]),
            make_navigate_step(step_index=2, from_url=FORM_URL, to_url=DASHBOARD_URL, friction_signals=["off_track_navigation"]),
            make_navigate_step(step_index=3, from_url=DASHBOARD_URL, to_url=START_URL, friction_signals=["off_track_navigation"]),
        ]
        issues = analyze_friction(steps)
        lost_issues = [i for i in issues if i.signal == "lost_navigation"]
        assert len(lost_issues) == 1
        assert lost_issues[0].severity == "medium"
        assert lost_issues[0].step_indexes == [1, 2, 3]

    def test_five_steps_high_severity(self):
        steps = [
            make_navigate_step(step_index=i, from_url=START_URL, to_url=FORM_URL, friction_signals=["off_track_navigation"])
            for i in range(1, 6)
        ]
        issues = analyze_friction(steps)
        lost_issues = [i for i in issues if i.signal == "lost_navigation"]
        assert len(lost_issues) == 1
        assert lost_issues[0].severity == "high"

    def test_no_off_track_signal(self):
        steps = [
            make_navigate_step(step_index=1, from_url=START_URL, to_url=FORM_URL),
        ]
        issues = analyze_friction(steps)
        lost_issues = [i for i in issues if i.signal == "lost_navigation"]
        assert lost_issues == []


# ============================ 误点 ============================ #


class TestMisclick:
    def test_click_execution_failure(self):
        steps = [
            make_click_step(step_index=1, execution_success=False),
        ]
        issues = analyze_friction(steps)
        misclick_issues = [i for i in issues if i.signal == "misclick"]
        assert len(misclick_issues) == 1
        assert misclick_issues[0].severity == "low"
        assert 1 in misclick_issues[0].step_indexes

    def test_click_page_error_after(self):
        steps = [
            make_click_step(step_index=1, after_error_messages=["请填写必填项"]),
        ]
        issues = analyze_friction(steps)
        misclick_issues = [i for i in issues if i.signal == "misclick"]
        assert len(misclick_issues) == 1

    def test_click_then_different_click_no_page_change(self):
        steps = [
            make_click_step(step_index=1, selector="#a", visible_text_summary="相同内容", after_text="相同内容"),
            make_click_step(step_index=2, selector="#b", visible_text_summary="相同内容", after_text="变化后内容"),
        ]
        issues = analyze_friction(steps)
        misclick_issues = [i for i in issues if i.signal == "misclick"]
        assert len(misclick_issues) == 1
        assert 1 in misclick_issues[0].step_indexes

    def test_click_then_different_click_with_page_change(self):
        steps = [
            make_click_step(step_index=1, selector="#a", after_text="内容A"),
            make_click_step(step_index=2, selector="#b", after_text="内容B"),
        ]
        issues = analyze_friction(steps)
        misclick_issues = [i for i in issues if i.signal == "misclick"]
        assert misclick_issues == []


# ============================ 混合场景 ============================ #


class TestMixedFriction:
    def test_multiple_friction_types(self):
        steps = [
            make_click_step(step_index=1, selector="#submit", url=START_URL, after_url=START_URL),
            make_click_step(step_index=2, selector="#submit", url=START_URL, after_url=START_URL),
            make_click_step(step_index=3, selector="#submit", url=START_URL, after_url=START_URL),
            make_navigate_step(step_index=4, from_url=START_URL, to_url=FORM_URL, friction_signals=["off_track_navigation"]),
        ]
        issues = analyze_friction(steps)
        signals = {i.signal for i in issues}
        assert "repeated_click" in signals
        assert "lost_navigation" in signals

    def test_suggested_fix_not_empty(self):
        steps = [
            make_click_step(step_index=1, execution_success=False),
        ]
        issues = analyze_friction(steps)
        assert len(issues) >= 1
        for issue in issues:
            if issue.signal == "misclick":
                assert issue.suggested_fix != ""


# ============================ RunReport 集成 ============================ #


class TestRunReportIntegration:
    def test_report_contains_friction_issues(self):
        from backend.analysis.report_builder import build_run_report_without_llm
        from backend.schemas.run_schemas import Persona, RunRecord, RunRequest, Task

        steps = [
            make_click_step(step_index=1, execution_success=True),
            make_click_step(step_index=2, execution_success=False, friction_signals=["action_failed"]),
            make_click_step(step_index=3, execution_success=True, validation_status="succeeded", friction_signals=[]),
        ]
        record = RunRecord(
            run_id="run-test",
            request=RunRequest(),
            persona=Persona(),
            task=Task(start_url=START_URL),
        )
        report = build_run_report_without_llm(record, steps)
        assert len(report.friction_issues) >= 1
        assert any(i.signal == "error_recovery" for i in report.friction_issues)

    def test_clean_report_has_empty_friction_issues(self):
        from backend.analysis.report_builder import build_run_report_without_llm
        from backend.schemas.run_schemas import Persona, RunRecord, RunRequest, Task

        steps = [
            make_click_step(step_index=1, validation_status="succeeded", detected_success=True, visible_text_summary="初始", after_text="成功"),
        ]
        record = RunRecord(
            run_id="run-clean",
            request=RunRequest(),
            persona=Persona(),
            task=Task(start_url=START_URL),
        )
        report = build_run_report_without_llm(record, steps)
        assert report.friction_issues == []

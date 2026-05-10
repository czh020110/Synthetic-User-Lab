from __future__ import annotations

import asyncio
from typing import Any, cast

from backend.analysis.validator import validate_progress
from backend.graph import demo_run_graph
from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    DemoPersona,
    DemoTask,
    ExecutionResult,
    ObservedPageState,
    StepLog,
    ValidationResult,
)

START_URL = "http://127.0.0.1:8000/demo/index.html"
OTHER_URL = "http://127.0.0.1:8000/demo/other.html"


def make_page_state(url: str = START_URL, text: str = "提交体验表单", errors: list[str] | None = None) -> ObservedPageState:
    return ObservedPageState(
        current_url=url,
        title="demo",
        visible_text_summary=text,
        clickable_elements=[],
        form_fields=[],
        error_messages=errors or [],
    )


def make_action(action: ActionName, target: str = "#start-demo", value: str | None = None) -> ActionInput:
    return ActionInput(action=action, target=target, value=value, reason="test")


def make_execution_result(
    action: ActionName,
    success: bool = True,
    detail: str = "ok",
    error_message: str | None = None,
    url: str = START_URL,
) -> ExecutionResult:
    return ExecutionResult(
        action=action,
        success=success,
        detail=detail,
        current_url_after_action=url,
        error_message=error_message,
    )


def make_step(
    step_index: int,
    *,
    url: str = START_URL,
    text: str = "提交体验表单",
    action: ActionName = "wait",
    target: str = "body",
    success: bool = True,
    detail: str = "ok",
    error_message: str | None = None,
) -> StepLog:
    observed_page_state = make_page_state(url=url, text=text)
    decided_action = make_action(action, target=target)
    execution_result = make_execution_result(action, success=success, detail=detail, error_message=error_message, url=url)
    validation_result = ValidationResult(status="running", should_stop=False, progress_summary="继续")
    return StepLog(
        step_index=step_index,
        observed_page_state=observed_page_state,
        decided_action=decided_action,
        execution_result=execution_result,
        validation_result=validation_result,
    )


def test_validate_progress_success() -> None:
    task = DemoTask(start_url=START_URL)
    page_state = make_page_state(text="提交成功")
    execution_result = make_execution_result("click")

    result = validate_progress(task, page_state, execution_result, [], 3)

    assert result.status == "succeeded"
    assert result.should_stop is True
    assert result.detected_success is True


def test_validate_progress_failed_action() -> None:
    task = DemoTask(start_url=START_URL)
    page_state = make_page_state()
    execution_result = make_execution_result("click", success=False, detail="failed", error_message="boom")

    result = validate_progress(task, page_state, execution_result, [], 1)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "action_failed" in result.friction_signals


def test_validate_progress_page_error() -> None:
    task = DemoTask(start_url=START_URL)
    page_state = make_page_state(errors=["字段校验失败"])
    execution_result = make_execution_result("click")

    result = validate_progress(task, page_state, execution_result, [], 1)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "page_error" in result.friction_signals


def test_validate_progress_step_limit() -> None:
    task = DemoTask(start_url=START_URL, max_steps=3)
    page_state = make_page_state()
    execution_result = make_execution_result("click")

    result = validate_progress(task, page_state, execution_result, [], 3)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "step_limit_reached" in result.friction_signals


def test_validate_progress_repeated_wait_requests_recovery() -> None:
    task = DemoTask(start_url=START_URL)
    previous_steps = [
        make_step(1, action="wait", target="body"),
        make_step(2, action="wait", target="body"),
    ]
    page_state = make_page_state()
    execution_result = make_execution_result("wait")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        3,
        current_action=make_action("wait", target="body"),
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert "repeated_wait" in result.friction_signals
    assert "recovery_candidate" in result.friction_signals


def test_validate_progress_repeated_wait_stops_after_threshold() -> None:
    task = DemoTask(start_url=START_URL)
    previous_steps = [
        make_step(1, action="wait", target="body"),
        make_step(2, action="wait", target="body"),
        make_step(3, action="wait", target="body"),
    ]
    page_state = make_page_state()
    execution_result = make_execution_result("wait")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        4,
        current_action=make_action("wait", target="body"),
    )

    assert result.status == "failed"
    assert result.should_stop is True
    assert "repeated_wait" in result.friction_signals


def test_validate_progress_repeated_action_target_requests_recovery() -> None:
    task = DemoTask(start_url=START_URL)
    previous_steps = [
        make_step(1, action="click", target="#start-demo"),
        make_step(2, action="click", target="#start-demo"),
    ]
    page_state = make_page_state()
    execution_result = make_execution_result("click")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        3,
        current_action=make_action("click", target="#start-demo"),
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert "repeated_action_target" in result.friction_signals
    assert "recovery_candidate" in result.friction_signals


def test_validate_progress_repeated_action_target_stops_after_threshold() -> None:
    task = DemoTask(start_url=START_URL)
    previous_steps = [
        make_step(1, action="click", target="#start-demo"),
        make_step(2, action="click", target="#start-demo"),
        make_step(3, action="click", target="#start-demo"),
    ]
    page_state = make_page_state()
    execution_result = make_execution_result("click")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        4,
        current_action=make_action("click", target="#start-demo"),
    )

    assert result.status == "failed"
    assert result.should_stop is True
    assert "repeated_action_target" in result.friction_signals


def test_validate_progress_stuck_page_requests_recovery() -> None:
    task = DemoTask(start_url=START_URL)
    previous_steps = [
        make_step(1, action="click", target="#start-demo"),
        make_step(2, action="click", target="#submit-demo"),
    ]
    page_state = make_page_state(text="提交体验表单")
    execution_result = make_execution_result("click")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        3,
        current_action=make_action("click", target="#submit-demo"),
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert "stuck_page" in result.friction_signals
    assert "recovery_candidate" in result.friction_signals


def test_validate_progress_off_track_requests_recovery() -> None:
    task = DemoTask(start_url=START_URL)
    previous_steps = [
        make_step(1, url=OTHER_URL, action="navigate", target=OTHER_URL),
        make_step(2, url=OTHER_URL, action="wait", target="body"),
    ]
    page_state = make_page_state(url=OTHER_URL, text="陌生页面")
    execution_result = make_execution_result("wait", url=OTHER_URL)

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        3,
        current_action=make_action("wait", target="body"),
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert "off_track_navigation" in result.friction_signals
    assert "recovery_candidate" in result.friction_signals


def test_validate_progress_agent_success_is_not_trusted_without_page_evidence() -> None:
    task = DemoTask(start_url=START_URL)
    page_state = make_page_state()
    execution_result = make_execution_result("wait")
    agent_validation = ValidationResult(
        status="succeeded",
        should_stop=True,
        progress_summary="agent thinks done",
        detected_success=True,
    )

    result = validate_progress(
        task,
        page_state,
        execution_result,
        [],
        1,
        current_action=make_action("wait", target="body"),
        agent_validation=agent_validation,
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert result.progress_summary == "尚未检测到任务成功条件，继续执行下一步。"


class FakeValidateAgent:
    async def ainvoke(self, *_args, **_kwargs):
        return {
            "structured_response": ValidationResult(
                status="succeeded",
                should_stop=True,
                progress_summary="agent thinks done",
                detected_success=True,
            ).model_dump()
        }


async def _fake_observe_page(_page):
    return make_page_state()


def test_validate_current_progress_applies_guardrails(monkeypatch) -> None:
    monkeypatch.setattr(demo_run_graph, "observe_page", _fake_observe_page)

    state = cast(Any, {
        "run_id": "run-1",
        "session": {"page": object()},
        "task": DemoTask(start_url=START_URL),
        "persona": DemoPersona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_action": make_action("wait", target="body"),
        "current_execution_result": make_execution_result("wait"),
        "validate_agent": FakeValidateAgent(),
    })

    result = asyncio.run(demo_run_graph.validate_current_progress(state))

    assert result["current_validation_result"].status == "running"
    assert result["current_validation_result"].should_stop is False
    assert result["should_stop"] is False


def test_route_after_log_uses_should_stop() -> None:
    assert demo_run_graph.route_after_log(cast(Any, {"should_stop": False})) == "observe_page"
    assert demo_run_graph.route_after_log(cast(Any, {"should_stop": True})) == "finalize_report"

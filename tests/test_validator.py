from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from backend.analysis.validator import validate_progress
import backend.graph.run_graph as run_graph
from backend.schemas.run_schemas import (
    ACTION_REGISTRY,
    ActionInput,
    ActionName,
    ClickActionPayload,
    ExecutionResult,
    FillActionPayload,
    NavigateActionPayload,
    ObservedPageState,
    Persona,
    PressActionPayload,
    RetrievedContextItem,
    RunRecord,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
    WaitActionPayload,
)
from backend.graph.wait_observer import WaitObservationResult, WaitObservationTrace
from backend.stores.in_memory_run_store import run_store

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


def make_action(action: ActionName, target: str | None = "#start-demo", value: str | int | None = None) -> ActionInput:
    if action == "navigate":
        payload = NavigateActionPayload(url=target if target is not None else START_URL)
    elif action == "click":
        payload = ClickActionPayload(selector=target if target is not None else "body")
    elif action == "fill":
        payload = FillActionPayload(
            selector=target if target is not None else "body",
            value=str(value) if value is not None else "test value",
        )
    elif action == "press":
        payload = PressActionPayload(key=target if target is not None else "Enter")
    else:
        payload = WaitActionPayload(duration_ms=int(value) if value is not None else 1000)
    return ActionInput(action=action, payload=payload, reason="test")


def make_execution_result(
    action: ActionName,
    success: bool = True,
    detail: str = "ok",
    error_message: str | None = None,
) -> ExecutionResult:
    return ExecutionResult(
        action=action,
        success=success,
        detail=detail,
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
    post_action_page_state = make_page_state(url=url, text=text)
    decided_action = make_action(action, target=target)
    execution_result = make_execution_result(action, success=success, detail=detail, error_message=error_message)
    validation_result = ValidationResult(status="running", should_stop=False, progress_summary="继续")
    return StepLog(
        step_index=step_index,
        observed_page_state=observed_page_state,
        decided_action=decided_action,
        execution_result=execution_result,
        validation_result=validation_result,
        post_action_page_state=post_action_page_state,
    )


def test_action_input_allows_wait_without_target() -> None:
    action = ActionInput(action="wait", payload=WaitActionPayload(duration_ms=2000), reason="test")

    assert action.action == "wait"
    assert isinstance(action.payload, WaitActionPayload)
    assert action.payload.duration_ms == 2000


def test_action_input_requires_fill_value() -> None:
    with pytest.raises(ValidationError):
        ActionInput(action="fill", payload=FillActionPayload(selector="#name", value=""), reason="test")


def test_route_after_execute_wait_goes_to_wait_node() -> None:
    state = cast(Any, {"current_action": make_action("wait", target=None, value=1000)})
    assert run_graph.route_after_execute(state) == "wait_after_action"


def test_route_after_execute_non_wait_goes_to_observe_after_action() -> None:
    state = cast(Any, {"current_action": make_action("click", target="#submit-demo")})
    assert run_graph.route_after_execute(state) == "observe_after_action"


def test_validate_progress_success() -> None:
    task = Task(start_url=START_URL)
    page_state = make_page_state(text="提交成功")
    execution_result = make_execution_result("click")
    agent_validation = ValidationResult(
        status="succeeded",
        should_stop=True,
        progress_summary="agent thinks done",
        detected_success=True,
    )

    result = validate_progress(task, page_state, execution_result, [], 3, agent_validation=agent_validation)

    assert result.status == "succeeded"
    assert result.should_stop is True
    assert result.detected_success is True


def test_validate_progress_success_at_step_limit_is_not_overridden() -> None:
    task = Task(start_url=START_URL, max_steps=3)
    page_state = make_page_state(text="提交成功")
    execution_result = make_execution_result("click")
    agent_validation = ValidationResult(
        status="succeeded",
        should_stop=True,
        progress_summary="agent thinks done",
        detected_success=True,
    )

    result = validate_progress(task, page_state, execution_result, [], 3, agent_validation=agent_validation)

    assert result.status == "succeeded"
    assert result.should_stop is True
    assert result.detected_success is True


def test_validate_progress_failed_action() -> None:
    task = Task(start_url=START_URL)
    page_state = make_page_state()
    execution_result = make_execution_result("click", success=False, detail="failed", error_message="boom")

    result = validate_progress(task, page_state, execution_result, [], 1)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "action_failed" in result.friction_signals


def test_validate_progress_page_error() -> None:
    task = Task(start_url=START_URL)
    page_state = make_page_state(errors=["字段校验失败"])
    execution_result = make_execution_result("click")

    result = validate_progress(task, page_state, execution_result, [], 1)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "page_error" in result.friction_signals


def test_validate_progress_step_limit() -> None:
    task = Task(start_url=START_URL, max_steps=3)
    page_state = make_page_state()
    execution_result = make_execution_result("click")

    result = validate_progress(task, page_state, execution_result, [], 3)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "step_limit_reached" in result.friction_signals


def test_validate_progress_repeated_wait_requests_recovery() -> None:
    task = Task(start_url=START_URL)
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
    task = Task(start_url=START_URL)
    previous_steps = [
        make_step(1, text="处理中 1", action="wait", target="body"),
        make_step(2, text="处理中 2", action="wait", target="body"),
        make_step(3, text="处理中 3", action="wait", target="body"),
    ]
    page_state = make_page_state(text="处理中 4")
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
    task = Task(start_url=START_URL)
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
    task = Task(start_url=START_URL)
    previous_steps = [
        make_step(1, text="步骤 1", action="click", target="#start-demo"),
        make_step(2, text="步骤 2", action="click", target="#start-demo"),
        make_step(3, text="步骤 3", action="click", target="#start-demo"),
    ]
    page_state = make_page_state(text="步骤 4")
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
    task = Task(start_url=START_URL)
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


def test_validate_progress_stuck_page_keeps_running_after_four_stable_steps() -> None:
    task = Task(start_url=START_URL)
    previous_steps = [
        make_step(1, action="click", target="#submit-demo"),
        make_step(2, action="click", target="#submit-demo"),
        make_step(3, action="click", target="#submit-demo"),
    ]
    page_state = make_page_state(text="提交体验表单")
    execution_result = make_execution_result("click")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        4,
        current_action=make_action("click", target="#submit-demo"),
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert "stuck_page" in result.friction_signals
    assert "recovery_candidate" in result.friction_signals


def test_validate_progress_off_track_requests_recovery() -> None:
    task = Task(start_url=START_URL)
    previous_steps = [
        make_step(1, url=OTHER_URL, action="navigate", target=OTHER_URL),
        make_step(2, url=OTHER_URL, action="wait", target="body"),
    ]
    page_state = make_page_state(url=OTHER_URL, text="陌生页面")
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
    assert "off_track_navigation" in result.friction_signals
    assert "recovery_candidate" in result.friction_signals


def test_validate_progress_agent_success_drives_completion() -> None:
    task = Task(start_url=START_URL)
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

    assert result.status == "succeeded"
    assert result.should_stop is True
    assert result.detected_success is True
    assert result.progress_summary == "agent thinks done"


def test_validate_progress_fill_does_not_mark_stuck_page() -> None:
    task = Task(start_url=START_URL)
    previous_steps = [
        make_step(1, text="姓名表单", action="fill", target="#name"),
        make_step(2, text="姓名表单", action="fill", target="#email"),
    ]
    page_state = make_page_state(text="姓名表单")
    execution_result = make_execution_result("fill")

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        3,
        current_action=make_action("fill", target="#comment", value="继续填写"),
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert "stuck_page" not in result.friction_signals
    assert "recovery_candidate" not in result.friction_signals


def test_validate_progress_soft_failed_agent_validation_keeps_running() -> None:
    task = Task(start_url=START_URL)
    page_state = make_page_state(text="仍可继续")
    execution_result = make_execution_result("click")
    agent_validation = ValidationResult(
        status="failed",
        should_stop=True,
        progress_summary="模型怀疑失败，但未确认。",
        friction_signals=["possible_issue"],
        detected_error=False,
    )

    result = validate_progress(
        task,
        page_state,
        execution_result,
        [],
        1,
        current_action=make_action("click", target="#submit-demo"),
        agent_validation=agent_validation,
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert result.progress_summary == "尚未出现可确认的失败条件，继续观察后续步骤。"
    assert "possible_issue" in result.friction_signals


@pytest.mark.parametrize(
    ("name", "previous_steps", "page_state", "current_action", "unexpected_signal"),
    [
        (
            "wait reset after click",
            [
                make_step(1, text="处理中 1", action="wait", target="body"),
                make_step(2, text="处理中 2", action="wait", target="body"),
                make_step(3, text="点击后页面", action="click", target="#submit-demo"),
            ],
            make_page_state(text="点击后继续等待"),
            make_action("wait", target="body"),
            "repeated_wait",
        ),
        (
            "action target reset after target change",
            [
                make_step(1, text="入口 A-1", action="click", target="#entry-a"),
                make_step(2, text="入口 A-2", action="click", target="#entry-a"),
                make_step(3, text="入口 B", action="click", target="#entry-b"),
            ],
            make_page_state(text="再次看到入口 A"),
            make_action("click", target="#entry-a"),
            "repeated_action_target",
        ),
        (
            "off track reset after returning start url",
            [
                make_step(1, url=OTHER_URL, text="陌生页面 1", action="navigate", target=OTHER_URL),
                make_step(2, url=OTHER_URL, text="陌生页面 2", action="wait", target="body"),
                make_step(3, url=START_URL, text="回到起点", action="navigate", target=START_URL),
            ],
            make_page_state(url=START_URL, text="回到起点后等待"),
            make_action("wait", target="body"),
            "off_track_navigation",
        ),
    ],
)
def test_validate_progress_streaks_reset_after_intervening_steps(
    name: str,
    previous_steps: list[StepLog],
    page_state: ObservedPageState,
    current_action: ActionInput,
    unexpected_signal: str,
) -> None:
    del name
    task = Task(start_url=START_URL)
    execution_result = make_execution_result(current_action.action)

    result = validate_progress(
        task,
        page_state,
        execution_result,
        previous_steps,
        len(previous_steps) + 1,
        current_action=current_action,
    )

    assert result.status == "running"
    assert result.should_stop is False
    assert unexpected_signal not in result.friction_signals


class FakeValidateAgent:
    async def ainvoke(self, *_args, **_kwargs):
        return {
            "raw": None,
            "parsed": ValidationResult(
                status="succeeded",
                should_stop=True,
                progress_summary="agent thinks done",
                detected_success=True,
            ),
            "parsing_error": None,
        }


class RecordingValidateAgent:
    def __init__(self) -> None:
        self.calls: list[list[Any]] = []

    async def ainvoke(self, payload, **_kwargs):
        # payload 现在是消息列表而不是 {"messages": [...]} dict
        self.calls.append(payload if isinstance(payload, list) else payload.get("messages", []))
        return {
            "raw": None,
            "parsed": ValidationResult(
                status="running",
                should_stop=False,
                progress_summary="继续观察",
            ),
            "parsing_error": None,
        }


class FailIfCalledValidateAgent:
    async def ainvoke(self, *_args, **_kwargs):
        raise AssertionError("validate agent should not be called")


async def _fake_observe_page(_page):
    return make_page_state()


def test_validate_current_progress_applies_guardrails(monkeypatch) -> None:
    monkeypatch.setattr(run_graph, "observe_page", _fake_observe_page)

    state = cast(Any, {
        "run_id": "run-1",
        "session": {"page": object()},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_action": make_action("wait", target="body"),
        "current_execution_result": make_execution_result("wait"),
        "validate_agent": FakeValidateAgent(),
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    assert result["current_validation_result"].status == "succeeded"
    assert result["current_validation_result"].should_stop is True
    assert result["should_stop"] is True


def test_validate_current_progress_passes_success_criteria_to_validate_agent() -> None:
    validate_agent = RecordingValidateAgent()
    state = cast(Any, {
        "run_id": "run-success-criteria",
        "session": {"page": object()},
        "task": Task(start_url=START_URL, success_criteria=["页面出现提交成功", "结果页出现摘要卡片"]),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_page_state": make_page_state(text="结果页已出现摘要卡片"),
        "current_action": make_action("click", target="#submit-demo"),
        "current_execution_result": make_execution_result("click"),
        "validate_agent": validate_agent,
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    assert result["current_validation_result"].status == "running"
    assert result["should_stop"] is False
    assert validate_agent.calls
    all_content = " ".join(msg.content for msg in validate_agent.calls[0])
    assert "success_criteria:" in all_content
    assert "页面出现提交成功" in all_content
    assert "结果页出现摘要卡片" in all_content


def test_validate_current_progress_passes_retrieval_context_to_validate_agent() -> None:
    validate_agent = RecordingValidateAgent()
    state = cast(Any, {
        "run_id": "run-validate-retrieval",
        "session": {"page": object()},
        "task": Task(start_url=START_URL, success_criteria=["页面出现提交成功"]),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_page_state": make_page_state(text="页面正在处理中"),
        "current_action": make_action("click", target="#submit-demo"),
        "current_execution_result": make_execution_result("click"),
        "validate_agent": validate_agent,
        "retrieval_context": [
            RetrievedContextItem(
                source_type="product_knowledge",
                title="正常等待提示",
                content="当页面显示正在处理、请稍候或加载中时，优先等待后端处理结束，再继续下一步。",
                source_ref="seed:product_knowledge:waiting_state",
            )
        ],
    })

    asyncio.run(run_graph.validate_current_progress(state))

    all_content = " ".join(msg.content for msg in validate_agent.calls[0])
    assert "retrieval_context:" in all_content
    assert "正常等待提示" in all_content
    assert "优先等待后端处理结束" in all_content


def test_wait_after_action_records_wait_observation(monkeypatch) -> None:
    page_state = make_page_state(text="提交成功")

    class FakePage:
        def __init__(self) -> None:
            self.url = START_URL
            self.screenshot_calls: list[str] = []

        async def screenshot(self, path: str, full_page: bool = True) -> None:
            del full_page
            self.screenshot_calls.append(path)

    fake_page = FakePage()

    async def fake_observe_until_ready(_page, *, classify_fn=None, observe_fn=None, capture_trace_screenshot_fn=None, options=None):
        del _page, classify_fn, observe_fn, options
        wait_screenshot = None
        if capture_trace_screenshot_fn is not None:
            wait_screenshot = await capture_trace_screenshot_fn(1)
        return WaitObservationResult(
            status="success",
            page_state=page_state,
            observations=3,
            reason="模型判断任务已经完成。",
            elapsed_ms=3000,
            timeout_ms=600000,
            terminal_decision="task_completed",
            traces=[
                WaitObservationTrace(
                    observation_index=1,
                    elapsed_ms=0,
                    normal_wait_elapsed_ms=0,
                    abnormal_wait_elapsed_ms=0,
                    decision="normal_waiting",
                    reason="仍在处理中。",
                    next_wait_ms=2000,
                    screenshot_path=wait_screenshot,
                )
            ],
        )

    monkeypatch.setattr(run_graph, "observe_until_ready", fake_observe_until_ready)
    state = cast(Any, {
        "session": {"page": fake_page},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "wait_agent": object(),
        "current_action": make_action("click", target="#submit-demo"),
        "current_execution_result": make_execution_result("click"),
        "current_step_index": 0,
        "screenshot_dir": Path("screenshots"),
        "run_id": "run-wait-observation",
    })

    result = asyncio.run(run_graph.wait_after_action(state))

    assert result["post_action_page_state"].screenshot_path.endswith("step-1-after.png")
    assert fake_page.screenshot_calls[-1].endswith("step-1-after.png")
    assert result["wait_observation_status"] == "success"
    assert result["wait_observation_reason"] == "模型判断任务已经完成。"
    assert result["wait_observation_observations"] == 3
    assert result["wait_observation_elapsed_ms"] == 3000
    assert result["wait_observation_timeout_ms"] == 600000
    assert result["wait_observation_terminal_decision"] == "task_completed"
    assert result["wait_observation_traces"] == [
        {
            "observation_index": 1,
            "elapsed_ms": 0,
            "normal_wait_elapsed_ms": 0,
            "abnormal_wait_elapsed_ms": 0,
            "decision": "normal_waiting",
            "reason": "仍在处理中。",
            "next_wait_ms": 2000,
            "screenshot_path": result["wait_observation_traces"][0]["screenshot_path"],
        }
    ]


def test_route_after_validate_enters_wait_on_recovery_candidate() -> None:
    state = cast(Any, {
        "current_validation_result": ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="继续观察",
            friction_signals=["stuck_page", "recovery_candidate"],
        ),
        "should_stop": False,
        "wait_observation_status": None,
    })

    assert run_graph.route_after_validate(state) == "wait_after_action"


@pytest.mark.parametrize("friction_signal", ["repeated_wait", "repeated_action_target", "off_track_navigation"])
def test_route_after_validate_enters_wait_for_other_recovery_candidates(friction_signal: str) -> None:
    state = cast(Any, {
        "current_validation_result": ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="继续观察",
            friction_signals=[friction_signal, "recovery_candidate"],
        ),
        "should_stop": False,
        "wait_observation_status": None,
    })

    assert run_graph.route_after_validate(state) == "wait_after_action"


def test_route_after_validate_logs_when_wait_already_happened() -> None:
    state = cast(Any, {
        "current_validation_result": ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="继续观察",
            friction_signals=["stuck_page", "recovery_candidate"],
        ),
        "should_stop": False,
        "wait_observation_status": "actionable",
    })

    assert run_graph.route_after_validate(state) == "log_step"


def test_validate_current_progress_uses_agent_after_actionable_wait() -> None:
    state = cast(Any, {
        "run_id": "run-actionable-wait",
        "session": {"page": object()},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_page_state": make_page_state(text="页面已有下一步入口"),
        "current_action": make_action("wait", target=None, value=1000),
        "current_execution_result": make_execution_result("wait"),
        "wait_observation_status": "actionable",
        "wait_observation_reason": "页面已有下一步入口。",
        "validate_agent": FakeValidateAgent(),
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    assert result["current_validation_result"].status == "succeeded"
    assert result["should_stop"] is True


def test_validate_current_progress_handles_normal_wait_timeout() -> None:
    state = cast(Any, {
        "run_id": "run-wait-timeout",
        "session": {"page": object()},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_page_state": make_page_state(text="正在注册，请稍候..."),
        "current_action": make_action("click", target="#submit-demo"),
        "current_execution_result": make_execution_result("click"),
        "wait_observation_status": "normal_timeout",
        "wait_observation_reason": "页面正常等待超过上限，仍未进入下一步或完成状态。",
        "validate_agent": FailIfCalledValidateAgent(),
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    validation = result["current_validation_result"]
    assert validation.status == "failed"
    assert validation.should_stop is True
    assert "wait_observe_normal_timeout" in validation.friction_signals
    assert result["should_stop"] is True


def test_validate_current_progress_handles_abnormal_stuck_timeout() -> None:
    state = cast(Any, {
        "run_id": "run-abnormal-stuck",
        "session": {"page": object()},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 0,
        "current_page_state": make_page_state(text="空白页面"),
        "current_action": make_action("wait", target=None, value=1000),
        "current_execution_result": make_execution_result("wait"),
        "wait_observation_status": "abnormal_stuck",
        "wait_observation_reason": "页面疑似异常卡住，连续 30 秒没有恢复为正常等待、可操作或完成状态。",
        "validate_agent": FailIfCalledValidateAgent(),
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    validation = result["current_validation_result"]
    assert validation.status == "running"
    assert validation.should_stop is False
    assert "wait_observe_abnormal_stuck" in validation.friction_signals
    assert "recovery_candidate" in validation.friction_signals
    assert result["should_stop"] is False


def test_validate_current_progress_stops_after_recovery_abnormal_stuck() -> None:
    state = cast(Any, {
        "run_id": "run-abnormal-stuck-after-recovery",
        "session": {"page": object()},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "step_logs": [],
        "current_step_index": 1,
        "current_page_state": make_page_state(text="空白页面"),
        "current_action": make_action("wait", target=None, value=1000),
        "current_execution_result": make_execution_result("wait"),
        "wait_observation_status": "abnormal_stuck",
        "wait_observation_reason": "恢复后仍卡住。",
        "recovery_attempted": True,
        "validate_agent": FailIfCalledValidateAgent(),
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    validation = result["current_validation_result"]
    assert validation.status == "failed"
    assert validation.should_stop is True
    assert "wait_observe_abnormal_stuck" in validation.friction_signals
    assert result["should_stop"] is True


def test_route_after_log_uses_should_stop() -> None:
    assert run_graph.route_after_log(cast(Any, {"should_stop": False})) == "observe_page"
    assert run_graph.route_after_log(cast(Any, {"should_stop": True})) == "finalize_report"


def test_route_after_log_prepares_recovery_after_abnormal_stuck() -> None:
    state = cast(Any, {
        "should_stop": False,
        "wait_observation_status": "abnormal_stuck",
        "current_validation_result": ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="准备恢复",
            friction_signals=["wait_observe_abnormal_stuck", "recovery_candidate"],
        ),
    })

    assert run_graph.route_after_log(state) == "prepare_recovery_action"


def test_prepare_recovery_action_builds_controlled_navigate() -> None:
    state = cast(Any, {
        "task": Task(start_url=START_URL),
        "current_page_state": make_page_state(text="空白页面"),
    })

    result = asyncio.run(run_graph.prepare_recovery_action(state))

    assert result["current_action"].action == "navigate"
    assert isinstance(result["current_action"].payload, NavigateActionPayload)
    assert result["current_action"].payload.url == START_URL
    assert result["current_page_state"].visible_text_summary == "空白页面"
    assert result["recovery_attempted"] is True
    assert result["wait_observation_status"] is None
    assert result["wait_observation_traces"] is None


def test_log_current_step_includes_wait_observation_details() -> None:
    run_store.clear()
    run_id = "run-wait-log"
    run_store.create_run(RunRecord(run_id=run_id, request=RunRequest(), persona=Persona(), task=Task(start_url=START_URL)))
    state = cast(Any, {
        "run_id": run_id,
        "step_before_page_state": make_page_state(text="提交前页面"),
        "post_action_page_state": make_page_state(text="提交成功"),
        "current_action": make_action("click", target="#submit-demo"),
        "current_execution_result": make_execution_result("click"),
        "current_validation_result": ValidationResult(
            status="succeeded",
            should_stop=True,
            progress_summary="完成",
            detected_success=True,
        ),
        "current_step_index": 0,
        "step_logs": [],
        "wait_observation_status": "success",
        "wait_observation_reason": "模型判断任务已经完成。",
        "wait_observation_observations": 2,
        "wait_observation_elapsed_ms": 2000,
        "wait_observation_timeout_ms": 600000,
        "wait_observation_terminal_decision": "task_completed",
        "wait_observation_traces": [
            {
                "observation_index": 1,
                "elapsed_ms": 0,
                "normal_wait_elapsed_ms": 0,
                "abnormal_wait_elapsed_ms": 0,
                "decision": "normal_waiting",
                "reason": "仍在处理中。",
                "next_wait_ms": 2000,
            },
            {
                "observation_index": 2,
                "elapsed_ms": 2000,
                "normal_wait_elapsed_ms": 2000,
                "abnormal_wait_elapsed_ms": 0,
                "decision": "task_completed",
                "reason": "已显示成功。",
                "next_wait_ms": 0,
            },
        ],
    })

    result = run_graph.log_current_step(state)
    step = result["step_logs"][0]

    assert step.wait_observation_status == "success"
    assert step.wait_observation_reason == "模型判断任务已经完成。"
    assert step.wait_observation_observations == 2
    assert step.wait_observation_traces[-1]["decision"] == "task_completed"


class FailingDecideAgent:
    def __init__(self) -> None:
        self.calls = 0

    async def ainvoke(self, *_args, **_kwargs):
        self.calls += 1
        raise RuntimeError("HTTP 401 invalid api key")


def test_decide_next_action_retries_agent_api_errors_before_model_error() -> None:
    decide_agent = FailingDecideAgent()
    state = cast(Any, {
        "run_id": "run-model-error",
        "current_page_state": make_page_state(),
        "persona": Persona(),
        "task": Task(start_url=START_URL),
        "step_logs": [],
        "decide_agent": decide_agent,
    })

    with pytest.raises(run_graph.ModelInvocationError) as exc_info:
        asyncio.run(run_graph.decide_next_action(state))

    assert decide_agent.calls == run_graph.MODEL_API_RETRY_LIMIT + 1
    assert exc_info.value.raw_message == "HTTP 401 invalid api key"


class BadFormatThenValidDecideAgent:
    def __init__(self) -> None:
        self.messages_by_call: list[list[Any]] = []

    async def ainvoke(self, payload, **_kwargs):
        # payload 现在是消息列表
        self.messages_by_call.append(payload if isinstance(payload, list) else payload.get("messages", []))
        if len(self.messages_by_call) == 1:
            return {
                "raw": None,
                "parsed": None,
                "parsing_error": ValidationError.from_exception_data(title="ActionInput", line_errors=[]),
            }
        return {
            "raw": None,
            "parsed": ActionInput(
                action="click",
                payload=ClickActionPayload(selector="#submit"),
                reason="格式修正后继续执行",
            ),
            "parsing_error": None,
        }


def test_decide_next_action_retries_bad_format_with_format_prompt() -> None:
    decide_agent = BadFormatThenValidDecideAgent()
    state = cast(Any, {
        "run_id": "run-format-retry",
        "current_page_state": make_page_state(),
        "persona": Persona(),
        "task": Task(start_url=START_URL),
        "step_logs": [],
        "retrieval_context": [
            RetrievedContextItem(
                source_type="failure_case",
                title="重复点击无进展",
                content="同一按钮重复点击多次仍没有变化时，不要继续重复操作，转向受控恢复路径。",
                source_ref="seed:failure_case:repeated_click",
            )
        ],
        "decide_agent": decide_agent,
    })

    result = asyncio.run(run_graph.decide_next_action(state))

    assert result["current_action"].action == "click"
    assert len(decide_agent.messages_by_call) == 2
    assert len(decide_agent.messages_by_call[1]) == len(decide_agent.messages_by_call[0]) + 1
    all_content_first_call = " ".join(msg.content for msg in decide_agent.messages_by_call[0])
    assert "retrieval_context:" in all_content_first_call
    assert "重复点击无进展" in all_content_first_call
    assert "转向受控恢复路径" in all_content_first_call
    assert "上一次回复未能通过结构化格式校验" in decide_agent.messages_by_call[1][-1].content
    assert "JSON Schema" in decide_agent.messages_by_call[1][-1].content


class AlwaysBadFormatDecideAgent:
    def __init__(self) -> None:
        self.calls = 0

    async def ainvoke(self, *_args, **_kwargs):
        self.calls += 1
        return {
            "raw": None,
            "parsed": None,
            "parsing_error": ValidationError.from_exception_data(title="ActionInput", line_errors=[]),
        }


def test_decide_next_action_stops_after_format_retry_limit() -> None:
    decide_agent = AlwaysBadFormatDecideAgent()
    state = cast(Any, {
        "run_id": "run-format-error",
        "current_page_state": make_page_state(),
        "persona": Persona(),
        "task": Task(start_url=START_URL),
        "step_logs": [],
        "decide_agent": decide_agent,
    })

    with pytest.raises(run_graph.ModelInvocationError) as exc_info:
        asyncio.run(run_graph.decide_next_action(state))

    assert decide_agent.calls == run_graph.MODEL_FORMAT_RETRY_LIMIT + 1
    assert "模型回复格式不正确" in exc_info.value.raw_message


class FakeModelErrorGraph:
    async def ainvoke(self, *_args, **_kwargs):
        raise run_graph.ModelInvocationError("decide", "HTTP 401 invalid api key")


def test_run_workflow_returns_raw_model_error_in_status_and_report(monkeypatch) -> None:
    run_store.clear()
    monkeypatch.setattr(run_graph, "build_run_graph", lambda _load_context_node: FakeModelErrorGraph())
    run_id = "run-model-error"
    run_store.create_run(
        RunRecord(
            run_id=run_id,
            request=RunRequest(),
            persona=Persona(),
            task=Task(start_url=START_URL),
        )
    )

    with pytest.raises(run_graph.ModelInvocationError):
        asyncio.run(
            run_graph.run_workflow(
                run_id=run_id,
                request=RunRequest(),
                app_base_url="http://127.0.0.1:8000",
                screenshot_dir=Path("screenshots"),
                load_context_node=object(),
            )
        )

    status = run_store.get_status(run_id)
    report = run_store.get_report(run_id)

    assert status is not None
    assert status.status == "failed"
    assert status.error_type == "model_error"
    assert status.error_message == "HTTP 401 invalid api key"
    assert report is not None
    assert report.error_type == "model_error"
    assert report.error_message == "HTTP 401 invalid api key"
    assert report.summary == "模型调用错误: HTTP 401 invalid api key"
    assert any("模型调用错误: HTTP 401 invalid api key" == item for item in report.key_findings)


# ============================ Action payload 契约回归 ============================ #


class TestActionPayloadContract:
    """覆盖 ActionInput / ACTION_REGISTRY 的 payload shape 正反例。"""

    def test_registry_contains_all_supported_actions(self) -> None:
        assert set(ACTION_REGISTRY.keys()) == {
            "navigate", "click", "fill", "wait",
            "press", "scroll", "upload", "select",
            "hover", "check", "uncheck", "dblclick",
            "drag", "ask_for_help", "abandon",
        }

    def test_navigate_payload_accepts_valid_url(self) -> None:
        action = ActionInput(action="navigate", payload=NavigateActionPayload(url="https://example.com"), reason="test")
        assert action.action == "navigate"
        assert isinstance(action.payload, NavigateActionPayload)
        assert action.payload.url == "https://example.com"

    def test_navigate_payload_rejects_empty_url(self) -> None:
        with pytest.raises(ValidationError):
            NavigateActionPayload(url="")

    def test_click_payload_accepts_valid_selector(self) -> None:
        action = ActionInput(action="click", payload=ClickActionPayload(selector="#submit"), reason="test")
        assert action.action == "click"
        assert isinstance(action.payload, ClickActionPayload)
        assert action.payload.selector == "#submit"

    def test_click_payload_rejects_empty_selector(self) -> None:
        with pytest.raises(ValidationError):
            ClickActionPayload(selector="")

    def test_click_payload_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            ClickActionPayload(**{"selector": "#btn", "value": "unexpected"})

    def test_fill_payload_accepts_selector_and_value(self) -> None:
        action = ActionInput(action="fill", payload=FillActionPayload(selector="#name", value="Alice"), reason="test")
        assert isinstance(action.payload, FillActionPayload)
        assert action.payload.selector == "#name"
        assert action.payload.value == "Alice"

    def test_fill_payload_rejects_empty_selector(self) -> None:
        with pytest.raises(ValidationError):
            FillActionPayload(selector="", value="test")

    def test_fill_payload_rejects_empty_value(self) -> None:
        with pytest.raises(ValidationError):
            FillActionPayload(selector="#name", value="")

    def test_fill_payload_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            FillActionPayload(**{"selector": "#name", "value": "test", "duration_ms": 1000})

    def test_wait_payload_defaults_duration_ms(self) -> None:
        action = ActionInput(action="wait", payload=WaitActionPayload(), reason="test")
        assert isinstance(action.payload, WaitActionPayload)
        assert action.payload.duration_ms == 1000

    def test_wait_payload_accepts_custom_duration(self) -> None:
        action = ActionInput(action="wait", payload=WaitActionPayload(duration_ms=3000), reason="test")
        assert isinstance(action.payload, WaitActionPayload)
        assert action.payload.duration_ms == 3000

    def test_wait_payload_rejects_negative_duration(self) -> None:
        with pytest.raises(ValidationError):
            WaitActionPayload(duration_ms=-1)

    def test_wait_payload_rejects_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            WaitActionPayload(**{"duration_ms": 1000, "value": "unexpected"})

    def test_action_input_normalizes_dict_payload_to_typed_model(self) -> None:
        action = ActionInput(action="click", payload=cast(Any, {"selector": "#btn"}), reason="test")
        assert isinstance(action.payload, ClickActionPayload)
        assert action.payload.selector == "#btn"

    def test_action_input_normalizes_fill_dict_payload(self) -> None:
        action = ActionInput(action="fill", payload=cast(Any, {"selector": "#name", "value": "Bob"}), reason="test")
        assert isinstance(action.payload, FillActionPayload)
        assert action.payload.value == "Bob"

    def test_action_input_rejects_mismatched_payload_type(self) -> None:
        with pytest.raises(ValidationError):
            ActionInput(action="click", payload=cast(Any, {"url": "https://example.com"}), reason="test")

    def test_action_input_rejects_unknown_action_name(self) -> None:
        with pytest.raises(ValidationError):
            ActionInput(action=cast(Any, "unknown_action"), payload=cast(Any, {}), reason="test")

    def test_action_input_rejects_extra_top_level_field(self) -> None:
        raw = {"action": "click", "payload": ClickActionPayload(selector="#btn").model_dump(), "reason": "test", "target": "#btn"}
        with pytest.raises(ValidationError):
            ActionInput.model_validate(raw)

    def test_action_input_rejects_old_flat_target_value(self) -> None:
        raw = {"action": "click", "target": "#btn", "value": "test", "reason": "test"}
        with pytest.raises(ValidationError):
            ActionInput.model_validate(raw)

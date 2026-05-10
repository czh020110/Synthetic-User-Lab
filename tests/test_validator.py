from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

import pytest

from backend.analysis.validator import validate_progress
import backend.graph.run_graph as run_graph
from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    ExecutionResult,
    ObservedPageState,
    Persona,
    RunRecord,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
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


def test_action_input_allows_wait_without_target() -> None:
    action = ActionInput(action="wait", target=None, value=2000, reason="test")

    assert action.action == "wait"
    assert action.target is None
    assert action.value == 2000


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


def test_wait_after_action_records_wait_observation(monkeypatch) -> None:
    page_state = make_page_state(text="提交成功")

    async def fake_observe_until_ready(_page, **_kwargs):
        return WaitObservationResult(
            "success",
            page_state,
            3,
            "模型判断任务已经完成。",
            [WaitObservationTrace(1, 0, "continue_waiting", "仍在处理中。")],
        )

    monkeypatch.setattr(run_graph, "observe_until_ready", fake_observe_until_ready)
    state = cast(Any, {
        "session": {"page": object()},
        "task": Task(start_url=START_URL),
        "persona": Persona(),
        "wait_agent": object(),
        "current_action": make_action("click", target="#submit-demo"),
    })

    result = asyncio.run(run_graph.wait_after_action(state))

    assert result["current_page_state"] == page_state
    assert result["wait_observation_status"] == "success"
    assert result["wait_observation_reason"] == "模型判断任务已经完成。"
    assert result["wait_observation_observations"] == 3
    assert result["wait_observation_traces"] == [
        {
            "observation_index": 1,
            "elapsed_ms": 0,
            "decision": "continue_waiting",
            "reason": "仍在处理中。",
        }
    ]


def test_route_after_validate_enters_wait_on_stuck_page() -> None:
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


def test_validate_current_progress_skips_agent_when_wait_observe_times_out() -> None:
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
        "wait_observation_status": "timeout",
        "wait_observation_reason": "等待页面进入可继续状态超时。",
        "validate_agent": FailIfCalledValidateAgent(),
    })

    result = asyncio.run(run_graph.validate_current_progress(state))

    validation = result["current_validation_result"]
    assert validation.status == "failed"
    assert validation.should_stop is True
    assert "wait_observe_timeout" in validation.friction_signals
    assert result["should_stop"] is True


def test_route_after_log_uses_should_stop() -> None:
    assert run_graph.route_after_log(cast(Any, {"should_stop": False})) == "observe_page"
    assert run_graph.route_after_log(cast(Any, {"should_stop": True})) == "finalize_report"


def test_log_current_step_includes_wait_observation_details() -> None:
    run_store.clear()
    run_id = "run-wait-log"
    run_store.create_run(RunRecord(run_id=run_id, request=RunRequest(), persona=Persona(), task=Task(start_url=START_URL)))
    state = cast(Any, {
        "run_id": run_id,
        "current_page_state": make_page_state(text="提交成功"),
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
        "wait_observation_traces": [
            {
                "observation_index": 1,
                "elapsed_ms": 0,
                "decision": "continue_waiting",
                "reason": "仍在处理中。",
            },
            {
                "observation_index": 2,
                "elapsed_ms": 2000,
                "decision": "task_completed",
                "reason": "已显示成功。",
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
        self.messages_by_call.append(payload["messages"])
        if len(self.messages_by_call) == 1:
            return {"structured_response": {"action": "invalid", "target": "#submit"}}
        return {
            "structured_response": ActionInput(
                action="click",
                target="#submit",
                reason="格式修正后继续执行",
            ).model_dump()
        }


def test_decide_next_action_retries_bad_format_with_format_prompt() -> None:
    decide_agent = BadFormatThenValidDecideAgent()
    state = cast(Any, {
        "run_id": "run-format-retry",
        "current_page_state": make_page_state(),
        "persona": Persona(),
        "task": Task(start_url=START_URL),
        "step_logs": [],
        "decide_agent": decide_agent,
    })

    result = asyncio.run(run_graph.decide_next_action(state))

    assert result["current_action"].action == "click"
    assert len(decide_agent.messages_by_call) == 2
    assert len(decide_agent.messages_by_call[1]) == len(decide_agent.messages_by_call[0]) + 1
    assert "上一次回复未能通过结构化格式校验" in decide_agent.messages_by_call[1][-1].content
    assert "JSON Schema" in decide_agent.messages_by_call[1][-1].content


class AlwaysBadFormatDecideAgent:
    def __init__(self) -> None:
        self.calls = 0

    async def ainvoke(self, *_args, **_kwargs):
        self.calls += 1
        return {"structured_response": {"action": "invalid", "target": "#submit"}}


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

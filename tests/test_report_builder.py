from __future__ import annotations

import asyncio
from typing import Any, cast

from backend.analysis import report_builder
from backend.analysis.report_builder import build_run_report, build_run_report_async, build_run_report_without_llm
from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    ClickActionPayload,
    ExecutionResult,
    FillActionPayload,
    NavigateActionPayload,
    ObservedPageState,
    Persona,
    RunRecord,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
    ValidationStatus,
)

START_URL = "http://127.0.0.1:8765/demo/index.html"


def make_record(persona: Persona | None = None) -> RunRecord:
    return RunRecord(
        run_id="run-1",
        request=RunRequest(),
        persona=persona or Persona(),
        task=Task(start_url=START_URL, name="验证任务", description="完成当前页面任务"),
    )


def make_step(
    *,
    step_index: int = 1,
    action: ActionName = "click",
    target: str = "#submit-demo",
    execution_success: bool = True,
    validation_status: ValidationStatus = "running",
    progress_summary: str = "继续",
    friction_signals: list[str] | None = None,
    detected_success: bool = False,
    detected_error: bool = False,
    execution_error_message: str | None = None,
) -> StepLog:
    return StepLog(
        step_index=step_index,
        observed_page_state=ObservedPageState(
            current_url=START_URL,
            title="demo",
            visible_text_summary="提交体验表单",
            clickable_elements=[],
            form_fields=[],
            error_messages=[],
        ),
        decided_action=ActionInput(action=cast(ActionName, action), payload=ClickActionPayload(selector=target), reason="test"),
        execution_result=ExecutionResult(
            action=cast(ActionName, action),
            success=execution_success,
            detail="ok" if execution_success else "failed",
            error_message=execution_error_message,
        ),
        validation_result=ValidationResult(
            status=cast(ValidationStatus, validation_status),
            should_stop=validation_status != "running",
            progress_summary=progress_summary,
            friction_signals=friction_signals or [],
            detected_success=detected_success,
            detected_error=detected_error,
        ),
        post_action_page_state=ObservedPageState(
            current_url=START_URL,
            title="demo",
            visible_text_summary="提交成功",
            clickable_elements=[],
            form_fields=[],
            error_messages=[],
        ),
    )


def test_build_run_report_skips_recommendations_when_no_obvious_issue(monkeypatch) -> None:
    def fail_if_called(*_args: Any, **_kwargs: Any):
        raise AssertionError("report analysis generator should not be called")

    monkeypatch.setattr(report_builder, "_generate_report_analysis", fail_if_called)

    record = make_record()
    steps = [
        make_step(
            validation_status="succeeded",
            progress_summary="页面已明确显示任务完成状态，任务完成。",
            detected_success=True,
        )
    ]

    report = build_run_report(record, steps)

    assert report.success is True
    assert report.conclusion == "keep"
    assert report.summary == "页面已明确显示任务完成状态，任务完成。"
    assert report.next_recommendations == []


def test_build_run_report_sets_must_fix_and_merges_detailed_findings(monkeypatch) -> None:
    monkeypatch.setattr(
        report_builder,
        "_generate_report_analysis",
        lambda **_kwargs: {
            "conclusion": "fix",
            "key_findings": ["第 2 步开始出现连续等待，任务推进被明显阻断。"],
            "next_recommendations": ["建议在等待阶段增加更直接的状态反馈，减少用户误以为页面无响应。"],
        },
    )

    record = make_record()
    steps = [
        make_step(step_index=1, progress_summary="继续"),
        make_step(
            step_index=2,
            validation_status="failed",
            progress_summary="页面连续等待后仍无进展。",
            friction_signals=["repeated_wait", "recovery_candidate"],
            detected_error=True,
            execution_success=False,
            execution_error_message="timeout",
        ),
    ]

    report = build_run_report(record, steps)

    assert report.success is False
    assert report.conclusion == "fix"
    assert any("首次明显问题出现在第 2 步" in item for item in report.key_findings)
    assert any("连续等待" in item for item in report.key_findings)
    assert report.next_recommendations == [
        "建议在等待阶段增加更直接的状态反馈，减少用户误以为页面无响应。"
    ]


def test_build_run_report_sets_needs_optimization_when_success_has_friction(monkeypatch) -> None:
    monkeypatch.setattr(
        report_builder,
        "_generate_report_analysis",
        lambda **_kwargs: {
            "conclusion": "optimize",
            "key_findings": ["虽然任务完成，但过程中存在重复等待和完成态确认不明确的问题。"],
            "next_recommendations": ["建议在完成态增加更直接的确认提示，帮助用户更快确认任务已结束。"],
        },
    )

    record = make_record()
    steps = [
        make_step(
            validation_status="succeeded",
            progress_summary="任务已完成，但中途等待较多。",
            friction_signals=["repeated_wait"],
            detected_success=True,
        )
    ]

    report = build_run_report(record, steps)

    assert report.success is True
    assert report.conclusion == "optimize"
    assert report.next_recommendations == [
        "建议在完成态增加更直接的确认提示，帮助用户更快确认任务已结束。"
    ]


def test_build_run_report_passes_persona_context_into_recommendations(monkeypatch) -> None:
    def analysis_stub(**kwargs: Any) -> dict[str, Any]:
        record: RunRecord = kwargs["record"]
        if record.persona.patience_level == "low":
            return {
                "conclusion": "optimize",
                "key_findings": ["低耐心用户在等待阶段更容易误判系统是否已完成。"],
                "next_recommendations": ["当前 persona 耐心较低，建议在等待阶段补充更即时的状态反馈。"],
            }
        return {
            "conclusion": "optimize",
            "key_findings": ["高耐心用户虽然会继续观察，但仍可能在完成态提示不足时迟疑。"],
            "next_recommendations": ["当前 persona 更有耐心，可优先优化任务完成态的确认信息。"],
        }

    monkeypatch.setattr(report_builder, "_generate_report_analysis", analysis_stub)

    low_patience_record = make_record(
        Persona(
            id="persona-low-patience",
            name="低耐心用户",
            description="等待时容易怀疑系统无响应。",
            skill_level="newbie",
            patience_level="low",
            risk_preference="low",
        )
    )
    patient_record = make_record(
        Persona(
            id="persona-patient",
            name="耐心用户",
            description="愿意多观察一步。",
            skill_level="newbie",
            patience_level="high",
            risk_preference="low",
        )
    )
    steps = [
        make_step(
            validation_status="failed",
            progress_summary="页面等待后仍无进展。",
            friction_signals=["repeated_wait"],
            detected_error=True,
        )
    ]

    low_patience_report = build_run_report(low_patience_record, steps)
    patient_report = build_run_report(patient_record, steps)

    assert low_patience_report.conclusion == "fix"
    assert patient_report.conclusion == "fix"
    assert low_patience_report.next_recommendations == [
        "当前 persona 耐心较低，建议在等待阶段补充更即时的状态反馈。"
    ]
    assert patient_report.next_recommendations == [
        "当前 persona 更有耐心，可优先优化任务完成态的确认信息。"
    ]


def test_build_run_report_without_llm_skips_detailed_generation(monkeypatch) -> None:
    def fail_if_called(*_args: Any, **_kwargs: Any):
        raise AssertionError("report analysis generator should not be called")

    monkeypatch.setattr(report_builder, "_generate_report_analysis", fail_if_called)

    record = make_record()
    steps = [
        make_step(
            validation_status="failed",
            progress_summary="页面等待后仍无进展。",
            friction_signals=["repeated_wait"],
            detected_error=True,
        )
    ]

    report = build_run_report_without_llm(record, steps)

    assert report.success is False
    assert report.conclusion == "fix"
    assert report.next_recommendations == []


class FakeAsyncReportLlm:
    def __init__(self) -> None:
        self.invoke_called = False
        self.ainvoke_called = False

    def invoke(self, _messages):
        self.invoke_called = True
        raise AssertionError("sync invoke should not be used in async report path")

    async def ainvoke(self, _messages):
        self.ainvoke_called = True

        class Response:
            content = '{"conclusion":"fix","key_findings":["异步分析发现"],"next_recommendations":["异步建议"]}'

        return Response()


def test_build_run_report_async_uses_async_llm(monkeypatch) -> None:
    fake_llm = FakeAsyncReportLlm()
    monkeypatch.setattr(report_builder, "_build_recommendation_llm", lambda: fake_llm)

    record = make_record()
    steps = [
        make_step(
            validation_status="failed",
            progress_summary="页面等待后仍无进展。",
            friction_signals=["repeated_wait"],
            detected_error=True,
        )
    ]

    report = asyncio.run(build_run_report_async(record, steps))

    assert fake_llm.ainvoke_called is True
    assert fake_llm.invoke_called is False
    assert "异步分析发现" in report.key_findings
    assert report.next_recommendations == ["异步建议"]


def test_step_details_serialize_payload_for_each_action_type() -> None:
    record = make_record()
    click_step = StepLog(
        step_index=1,
        observed_page_state=ObservedPageState(
            current_url=START_URL, title="demo", visible_text_summary="页面",
            clickable_elements=[], form_fields=[], error_messages=[],
        ),
        decided_action=ActionInput(action="click", payload=ClickActionPayload(selector="#btn"), reason="点击按钮"),
        execution_result=ExecutionResult(action="click", success=True, detail="ok"),
        validation_result=ValidationResult(status="running", should_stop=False, progress_summary="继续"),
        post_action_page_state=ObservedPageState(
            current_url=START_URL, title="demo", visible_text_summary="点击后",
            clickable_elements=[], form_fields=[], error_messages=[],
        ),
    )
    fill_step = StepLog(
        step_index=2,
        observed_page_state=ObservedPageState(
            current_url=START_URL, title="demo", visible_text_summary="表单",
            clickable_elements=[], form_fields=[], error_messages=[],
        ),
        decided_action=ActionInput(action="fill", payload=FillActionPayload(selector="#input", value="test"), reason="填写输入框"),
        execution_result=ExecutionResult(action="fill", success=True, detail="ok"),
        validation_result=ValidationResult(status="running", should_stop=False, progress_summary="继续"),
        post_action_page_state=ObservedPageState(
            current_url=START_URL, title="demo", visible_text_summary="填写后",
            clickable_elements=[], form_fields=[], error_messages=[],
        ),
    )
    navigate_step = StepLog(
        step_index=3,
        observed_page_state=ObservedPageState(
            current_url=START_URL, title="demo", visible_text_summary="导航前",
            clickable_elements=[], form_fields=[], error_messages=[],
        ),
        decided_action=ActionInput(action="navigate", payload=NavigateActionPayload(url=START_URL), reason="导航"),
        execution_result=ExecutionResult(action="navigate", success=True, detail="ok"),
        validation_result=ValidationResult(status="succeeded", should_stop=True, progress_summary="完成", detected_success=True),
        post_action_page_state=ObservedPageState(
            current_url=START_URL, title="demo", visible_text_summary="完成",
            clickable_elements=[], form_fields=[], error_messages=[],
        ),
    )

    report = build_run_report_without_llm(record, [click_step, fill_step, navigate_step])

    assert report.step_details[0]["action"] == "click"
    assert report.step_details[0]["payload"] == {"selector": "#btn"}
    assert report.step_details[1]["action"] == "fill"
    assert report.step_details[1]["payload"] == {"selector": "#input", "value": "test"}
    assert report.step_details[2]["action"] == "navigate"
    assert report.step_details[2]["payload"] == {"url": START_URL}

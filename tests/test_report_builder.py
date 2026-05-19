from __future__ import annotations

from typing import Any, cast

from backend.analysis import report_builder
from backend.analysis.report_builder import build_run_report
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
        decided_action=ActionInput(action=cast(ActionName, action), target=target, reason="test"),
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

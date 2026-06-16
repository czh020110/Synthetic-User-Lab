from __future__ import annotations

from typing import Any, cast

from backend.analysis import report_builder
from backend.analysis.report_builder import (
    _extract_key_screenshots,
    build_run_report,
    build_run_report_without_llm,
)
from backend.analysis.report_renderer import render_report_markdown
from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    ClickActionPayload,
    ExecutionResult,
    KeyScreenshot,
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
    before_screenshot: str | None = None,
    after_screenshot: str | None = None,
    wait_observation_status: str | None = None,
    wait_observation_traces: list[dict[str, Any]] | None = None,
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
            screenshot_path=before_screenshot,
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
            screenshot_path=after_screenshot,
        ),
        wait_observation_status=wait_observation_status,
        wait_observation_traces=wait_observation_traces or [],
    )


# ============================ 关键截图提取测试 ============================ #


def test_extract_key_screenshots_success_run() -> None:
    """成功 run 应包含起始页面和任务成功确认截图。"""

    steps = [
        make_step(step_index=1, before_screenshot="step-1-before.png", after_screenshot="step-1-after.png"),
        make_step(
            step_index=2,
            validation_status="succeeded",
            detected_success=True,
            before_screenshot="step-2-before.png",
            after_screenshot="step-2-after.png",
        ),
    ]

    screenshots = _extract_key_screenshots(steps, success=True)

    labels = [ks.label for ks in screenshots]
    assert "起始页面" in labels
    assert "任务成功确认" in labels

    # 起始页面来自第一步 before_action
    start_ks = next(ks for ks in screenshots if ks.label == "起始页面")
    assert start_ks.path == "step-1-before.png"
    assert start_ks.source == "before_action"

    # 成功确认来自最后一步 after_action
    success_ks = next(ks for ks in screenshots if ks.label == "任务成功确认")
    assert success_ks.path == "step-2-after.png"
    assert success_ks.source == "after_action"


def test_extract_key_screenshots_error_step() -> None:
    """包含报错步骤时应提取首次报错页面截图。"""

    steps = [
        make_step(step_index=1, before_screenshot="step-1-before.png"),
        make_step(
            step_index=2,
            detected_error=True,
            before_screenshot="step-2-before.png",
            after_screenshot="step-2-after.png",
        ),
    ]

    screenshots = _extract_key_screenshots(steps, success=False)

    labels = [ks.label for ks in screenshots]
    assert "首次报错页面" in labels

    error_ks = next(ks for ks in screenshots if ks.label == "首次报错页面")
    assert error_ks.step_index == 2
    assert error_ks.path == "step-2-before.png"


def test_extract_key_screenshots_recovery_step() -> None:
    """包含 recovery_candidate 摩擦信号时应提取恢复尝试起点截图。"""

    steps = [
        make_step(step_index=1, before_screenshot="step-1-before.png"),
        make_step(
            step_index=2,
            friction_signals=["recovery_candidate"],
            before_screenshot="step-2-before.png",
        ),
    ]

    screenshots = _extract_key_screenshots(steps, success=False)

    labels = [ks.label for ks in screenshots]
    assert "恢复尝试起点" in labels

    recovery_ks = next(ks for ks in screenshots if ks.label == "恢复尝试起点")
    assert recovery_ks.step_index == 2


def test_extract_key_screenshots_wait_abnormal_stuck() -> None:
    """包含 abnormal_stuck 等待观察时应提取等待观察截图。"""

    steps = [
        make_step(step_index=1, before_screenshot="step-1-before.png"),
        make_step(
            step_index=2,
            before_screenshot="step-2-before.png",
            wait_observation_status="abnormal_stuck",
            wait_observation_traces=[
                {"screenshot_path": "step-2-wait-1.png", "observation": "still loading"},
            ],
        ),
    ]

    screenshots = _extract_key_screenshots(steps, success=False)

    labels = [ks.label for ks in screenshots]
    assert "异常等待状态" in labels

    wait_ks = next(ks for ks in screenshots if ks.label == "异常等待状态")
    assert wait_ks.path == "step-2-wait-1.png"
    assert wait_ks.source == "wait_observation"


def test_extract_key_screenshots_skips_none_paths() -> None:
    """screenshot_path 为 None 时应跳过，不应报错。"""

    steps = [
        make_step(step_index=1, before_screenshot=None, after_screenshot=None),
    ]

    screenshots = _extract_key_screenshots(steps, success=False)

    # 起始页面截图为 None，应被跳过
    assert all(ks.path is not None for ks in screenshots)
    # 没有 None 路径的截图
    assert len(screenshots) == 0


def test_extract_key_screenshots_dedupes_same_path() -> None:
    """相同路径不应重复出现在关键截图列表中。"""

    same_path = "step-1-before.png"
    steps = [
        make_step(
            step_index=1,
            before_screenshot=same_path,
            after_screenshot=same_path,
            detected_error=True,
        ),
    ]

    screenshots = _extract_key_screenshots(steps, success=False)

    paths = [ks.path for ks in screenshots]
    assert len(paths) == len(set(paths)), f"重复路径: {paths}"


def test_extract_key_screenshots_empty_steps() -> None:
    """空步骤列表应返回空截图列表。"""

    assert _extract_key_screenshots([], success=False) == []


# ============================ 报告集成测试 ============================ #


def test_build_report_includes_key_screenshots() -> None:
    """build_run_report 应在最终报告中包含 key_screenshots。"""

    record = make_record()
    steps = [
        make_step(
            step_index=1,
            before_screenshot="step-1-before.png",
            after_screenshot="step-1-after.png",
            validation_status="succeeded",
            detected_success=True,
            progress_summary="任务完成",
        ),
    ]

    report = build_run_report_without_llm(record, steps)

    assert report.key_screenshots is not None
    labels = [ks.label for ks in report.key_screenshots]
    assert "起始页面" in labels
    assert "任务成功确认" in labels

    # structured_facts 也应包含 key_screenshots
    assert report.structured_facts is not None
    assert "key_screenshots" in report.structured_facts


# ============================ Markdown 渲染测试 ============================ #


def test_render_report_markdown_contains_key_sections() -> None:
    """Markdown 渲染应包含关键章节。"""

    record = make_record()
    steps = [
        make_step(
            step_index=1,
            before_screenshot="step-1-before.png",
            after_screenshot="step-1-after.png",
            validation_status="succeeded",
            detected_success=True,
            progress_summary="任务完成",
        ),
    ]

    report = build_run_report_without_llm(record, steps)
    md = render_report_markdown(report)

    assert "# Synthetic User Lab Run Report" in md
    assert "## 基本信息" in md
    assert "## Persona" in md
    assert "## 任务" in md
    assert "## 执行摘要" in md
    assert "run-1" in md
    assert "起始页面" in md
    assert "任务成功确认" in md


def test_render_report_markdown_includes_friction_issues() -> None:
    """包含摩擦问题时 Markdown 应包含摩擦问题章节。"""

    record = make_record()
    steps = [
        make_step(step_index=1, progress_summary="继续"),
        make_step(
            step_index=2,
            friction_signals=["repeated_click"],
            detected_error=True,
            execution_success=False,
            progress_summary="点击失败",
        ),
    ]

    report = build_run_report_without_llm(record, steps)
    md = render_report_markdown(report)

    assert "## 摩擦问题" in md


def test_render_report_markdown_includes_step_table() -> None:
    """Markdown 应包含步骤明细表格。"""

    record = make_record()
    steps = [
        make_step(
            step_index=1,
            validation_status="succeeded",
            detected_success=True,
            progress_summary="完成",
        ),
    ]

    report = build_run_report_without_llm(record, steps)
    md = render_report_markdown(report)

    assert "## 步骤明细" in md
    assert "| 步骤 | 动作 | 执行 | 验证 | 摩擦信号 |" in md
    assert "| 1 | click |" in md


def test_render_report_markdown_includes_error() -> None:
    """包含错误信息时 Markdown 应包含错误信息章节。"""

    record = make_record()
    record.error_type = "system_error"
    record.error_message = "浏览器连接超时"
    steps = [
        make_step(step_index=1, detected_error=True, progress_summary="失败"),
    ]

    report = build_run_report_without_llm(record, steps)
    md = render_report_markdown(report)

    assert "## 错误信息" in md
    assert "浏览器连接超时" in md

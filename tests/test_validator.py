from backend.analysis.validator import validate_progress
from backend.schemas.run_schemas import DemoTask, ExecutionResult, ObservedPageState


def test_validate_progress_success() -> None:
    task = DemoTask(start_url="http://127.0.0.1:8000/demo/index.html")
    page_state = ObservedPageState(
        current_url=task.start_url,
        title="success",
        visible_text_summary="提交成功",
        clickable_elements=[],
        form_fields=[],
        error_messages=[],
    )
    execution_result = ExecutionResult(action="click", success=True, detail="ok")

    result = validate_progress(task, page_state, execution_result, [], 3)

    assert result.status == "succeeded"
    assert result.should_stop is True
    assert result.detected_success is True


def test_validate_progress_failed_action() -> None:
    task = DemoTask(start_url="http://127.0.0.1:8000/demo/index.html")
    page_state = ObservedPageState(
        current_url=task.start_url,
        title="form",
        visible_text_summary="提交体验表单",
        clickable_elements=[],
        form_fields=[],
        error_messages=[],
    )
    execution_result = ExecutionResult(action="click", success=False, detail="failed", error_message="boom")

    result = validate_progress(task, page_state, execution_result, [], 1)

    assert result.status == "failed"
    assert result.should_stop is True
    assert "action_failed" in result.friction_signals

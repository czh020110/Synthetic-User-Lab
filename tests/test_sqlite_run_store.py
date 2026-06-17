from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from typing import Any, cast

import pytest

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
    RunStatusResponse,
    StepLog,
    Task,
    ValidationResult,
    ValidationStatus,
)
from backend.stores.sqlite_run_store import SqliteRunStore

START_URL = "http://127.0.0.1:8765/demo/index.html"


def make_record(run_id: str = "run-1") -> RunRecord:
    return RunRecord(
        run_id=run_id,
        request=RunRequest(),
        persona=Persona(),
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
    before_screenshot: str | None = None,
    after_screenshot: str | None = None,
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
        decided_action=ActionInput(
            action=cast(ActionName, action),
            payload=ClickActionPayload(selector=target),
            reason="test",
        ),
        execution_result=ExecutionResult(
            action=cast(ActionName, action),
            success=execution_success,
            detail="ok" if execution_success else "failed",
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
    )


@pytest.fixture
def store() -> SqliteRunStore:
    """创建使用临时文件的 SqliteRunStore 实例。"""

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    s = SqliteRunStore(db_path)
    s.initialize()
    yield s
    s.close()
    os.unlink(db_path)


# ============================ 生命周期测试 ============================ #


def test_full_lifecycle_success(store: SqliteRunStore) -> None:
    """成功 run 完整生命周期：create → mark_running → add_step → complete_run → get。"""

    record = make_record()
    store.create_run(record)
    store.mark_running(record.run_id)

    step = make_step(
        step_index=1,
        before_screenshot="step-1.png",
        after_screenshot="step-1-after.png",
        validation_status="succeeded",
        detected_success=True,
        progress_summary="任务完成",
    )
    store.add_step(record.run_id, step)

    # 构建最小 RunReport
    from backend.analysis.report_builder import build_run_report_without_llm

    report = build_run_report_without_llm(record, [step])
    store.complete_run(record.run_id, report)

    # 验证读取
    got_record = store.get_record(record.run_id)
    assert got_record is not None
    assert got_record.status == "succeeded"
    assert got_record.run_id == record.run_id

    got_status = store.get_status(record.run_id)
    assert got_status is not None
    assert got_status.status == "succeeded"

    got_steps = store.get_steps(record.run_id)
    assert got_steps is not None
    assert len(got_steps) == 1
    assert got_steps[0].step_index == 1
    # 截图路径正确持久化
    assert got_steps[0].observed_page_state.screenshot_path == "step-1.png"
    assert got_steps[0].post_action_page_state.screenshot_path == "step-1-after.png"

    got_report = store.get_report(record.run_id)
    assert got_report is not None
    assert got_report.run_id == record.run_id
    assert got_report.success is True


def test_full_lifecycle_failure(store: SqliteRunStore) -> None:
    """失败路径：create → mark_running → fail_run。"""

    record = make_record()
    store.create_run(record)
    store.mark_running(record.run_id)

    step = make_step(step_index=1, execution_success=False, validation_status="failed", progress_summary="失败")
    store.add_step(record.run_id, step)

    store.fail_run(record.run_id, "浏览器连接超时")

    got_record = store.get_record(record.run_id)
    assert got_record is not None
    assert got_record.status == "failed"
    assert got_record.error_message == "浏览器连接超时"
    assert got_record.error_type == "system_error"

    got_status = store.get_status(record.run_id)
    assert got_status is not None
    assert got_status.status == "failed"
    assert got_status.error_message == "浏览器连接超时"


# ============================ INSERT OR REPLACE 测试 ============================ #


def test_create_run_overwrites_existing(store: SqliteRunStore) -> None:
    """同一 run_id 调用两次 create_run，第二次应覆盖第一次。"""

    record1 = make_record()
    store.create_run(record1)

    # 添加步骤
    step = make_step(step_index=1)
    store.add_step(record1.run_id, step)

    # 第二次 create_run 应覆盖记录并清空步骤
    record2 = make_record(run_id=record1.run_id)
    record2.persona.name = "覆盖后的 persona"
    store.create_run(record2)

    got = store.get_record(record1.run_id)
    assert got is not None
    assert got.persona.name == "覆盖后的 persona"

    # 步骤应被清空
    got_steps = store.get_steps(record1.run_id)
    assert got_steps is not None
    assert len(got_steps) == 0


def test_create_run_preserves_created_at(store: SqliteRunStore) -> None:
    """重复 create_run 应保留原始 created_at，不被新记录的时间覆盖。"""

    record1 = make_record()
    original_created_at = record1.created_at
    store.create_run(record1)

    # 第二次 create_run 使用新 RunRecord（其 created_at 由 default_factory 生成，值不同）
    record2 = make_record(run_id=record1.run_id)
    # record2 的 created_at 是新的 default_factory 值
    store.create_run(record2)

    got = store.get_record(record1.run_id)
    assert got is not None
    # created_at 应保留第一次写入的值，而非第二次 default_factory 的新值
    assert got.created_at == original_created_at


# ============================ 持久化验证 ============================ #


def test_persistence_across_reopen() -> None:
    """关闭连接后重新打开，数据应持久化保存。"""

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # 第一次打开，写入数据
        store1 = SqliteRunStore(db_path)
        store1.initialize()
        record = make_record()
        store1.create_run(record)
        store1.mark_running(record.run_id)
        step = make_step(step_index=1)
        store1.add_step(record.run_id, step)
        store1.close()

        # 第二次打开，验证数据持久化
        store2 = SqliteRunStore(db_path)
        store2.initialize()
        got_record = store2.get_record(record.run_id)
        assert got_record is not None
        assert got_record.status == "running"
        assert got_record.run_id == record.run_id

        got_steps = store2.get_steps(record.run_id)
        assert got_steps is not None
        assert len(got_steps) == 1

        store2.close()
    finally:
        os.unlink(db_path)


# ============================ get_status 测试 ============================ #


def test_get_status_returns_correct_structure(store: SqliteRunStore) -> None:
    """get_status 应返回正确的 RunStatusResponse 结构。"""

    record = make_record()
    store.create_run(record)

    status = store.get_status(record.run_id)
    assert status is not None
    assert isinstance(status, RunStatusResponse)
    assert status.run_id == record.run_id
    assert status.status == "queued"
    assert status.error_type is None
    assert status.error_message is None


# ============================ 不存在的 run_id 测试 ============================ #


def test_get_nonexistent_run_returns_none(store: SqliteRunStore) -> None:
    """不存在的 run_id 应返回 None。"""

    assert store.get_record("nonexistent") is None
    assert store.get_status("nonexistent") is None
    assert store.get_steps("nonexistent") is None
    assert store.get_report("nonexistent") is None


# ============================ clear 测试 ============================ #


def test_clear_empties_all_data(store: SqliteRunStore) -> None:
    """clear() 应清空所有数据。"""

    record = make_record()
    store.create_run(record)
    step = make_step(step_index=1)
    store.add_step(record.run_id, step)

    store.clear()

    assert store.get_record(record.run_id) is None
    assert store.get_steps(record.run_id) is None
    assert store.get_report(record.run_id) is None


# ============================ 截图路径持久化测试 ============================ #


def test_screenshot_paths_persisted_in_steps(store: SqliteRunStore) -> None:
    """截图路径应通过 step_json 正确持久化。"""

    record = make_record()
    store.create_run(record)

    step = make_step(
        step_index=1,
        before_screenshot="screenshots/before-1.png",
        after_screenshot="screenshots/after-1.png",
    )
    store.add_step(record.run_id, step)

    got_steps = store.get_steps(record.run_id)
    assert got_steps is not None
    assert len(got_steps) == 1
    assert got_steps[0].observed_page_state.screenshot_path == "screenshots/before-1.png"
    assert got_steps[0].post_action_page_state.screenshot_path == "screenshots/after-1.png"


# ============================ key_screenshots 持久化测试 ============================ #


def test_key_screenshots_persisted_in_report(store: SqliteRunStore) -> None:
    """key_screenshots 应通过 report_json 正确持久化。"""

    from backend.analysis.report_builder import build_run_report_without_llm

    record = make_record()
    store.create_run(record)

    step = make_step(
        step_index=1,
        before_screenshot="step-1.png",
        after_screenshot="step-1-after.png",
        validation_status="succeeded",
        detected_success=True,
        progress_summary="完成",
    )
    store.add_step(record.run_id, step)

    report = build_run_report_without_llm(record, [step])
    store.complete_run(record.run_id, report)

    got_report = store.get_report(record.run_id)
    assert got_report is not None
    assert len(got_report.key_screenshots) > 0
    labels = [ks.label for ks in got_report.key_screenshots]
    assert "起始页面" in labels


# ============================ 多步骤测试 ============================ #


def test_multiple_steps_preserved_in_order(store: SqliteRunStore) -> None:
    """多步骤应按 step_index 顺序持久化。"""

    record = make_record()
    store.create_run(record)

    for i in range(1, 4):
        step = make_step(step_index=i, progress_summary=f"步骤 {i}")
        store.add_step(record.run_id, step)

    got_steps = store.get_steps(record.run_id)
    assert got_steps is not None
    assert len(got_steps) == 3
    assert [s.step_index for s in got_steps] == [1, 2, 3]


# ============================ :memory: 模式测试 ============================ #


def test_memory_mode_works() -> None:
    """:memory: 模式应正常工作。"""

    store = SqliteRunStore(":memory:")
    store.initialize()

    record = make_record()
    store.create_run(record)
    got = store.get_record(record.run_id)
    assert got is not None
    assert got.run_id == record.run_id

    store.close()

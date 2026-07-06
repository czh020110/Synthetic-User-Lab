from __future__ import annotations

import os
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
from backend.stores.postgres_run_store import PostgresRunStore

START_URL = "http://127.0.0.1:8765/demo/index.html"
POSTGRES_TEST_DSN_ENV = "SYNTHETIC_USER_LAB_POSTGRES_TEST_DSN"


def _postgres_test_dsn() -> str:
    dsn = os.getenv(POSTGRES_TEST_DSN_ENV)
    if not dsn:
        pytest.skip(f"{POSTGRES_TEST_DSN_ENV} is not configured")
    return dsn


def make_record(run_id: str = "pg-run-1") -> RunRecord:
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
def store() -> PostgresRunStore:
    store = PostgresRunStore(_postgres_test_dsn())
    store.initialize()
    store.clear()
    yield store
    store.clear()
    store.close()


def test_full_lifecycle_success(store: PostgresRunStore) -> None:
    record = make_record()
    store.create_run(record)
    store.mark_running(record.run_id)

    step = make_step(
        step_index=1,
        before_screenshot="pg-step-1.png",
        after_screenshot="pg-step-1-after.png",
        validation_status="succeeded",
        detected_success=True,
        progress_summary="任务完成",
    )
    store.add_step(record.run_id, step)

    from backend.analysis.report_builder import build_run_report_without_llm

    report = build_run_report_without_llm(record, [step])
    store.complete_run(record.run_id, report)

    got_record = store.get_record(record.run_id)
    assert got_record is not None
    assert got_record.status == "succeeded"

    got_status = store.get_status(record.run_id)
    assert got_status is not None
    assert got_status.status == "succeeded"

    got_steps = store.get_steps(record.run_id)
    assert got_steps is not None
    assert len(got_steps) == 1
    assert got_steps[0].observed_page_state.screenshot_path == "pg-step-1.png"
    assert got_steps[0].post_action_page_state.screenshot_path == "pg-step-1-after.png"

    got_report = store.get_report(record.run_id)
    assert got_report is not None
    assert got_report.run_id == record.run_id
    assert got_report.success is True


def test_full_lifecycle_failure(store: PostgresRunStore) -> None:
    record = make_record(run_id="pg-run-fail")
    store.create_run(record)
    store.mark_running(record.run_id)
    store.add_step(record.run_id, make_step(step_index=1, execution_success=False, validation_status="failed", progress_summary="失败"))

    store.fail_run(record.run_id, "浏览器连接超时")

    got_record = store.get_record(record.run_id)
    assert got_record is not None
    assert got_record.status == "failed"
    assert got_record.error_message == "浏览器连接超时"
    assert got_record.error_type == "system_error"


def test_create_run_overwrites_existing_and_clears_steps(store: PostgresRunStore) -> None:
    record1 = make_record(run_id="pg-run-overwrite")
    store.create_run(record1)
    store.add_step(record1.run_id, make_step(step_index=1))

    record2 = make_record(run_id=record1.run_id)
    record2.persona.name = "覆盖后的 persona"
    store.create_run(record2)

    got = store.get_record(record1.run_id)
    assert got is not None
    assert got.persona.name == "覆盖后的 persona"
    got_steps = store.get_steps(record1.run_id)
    assert got_steps is not None
    assert got_steps == []


def test_create_run_preserves_created_at(store: PostgresRunStore) -> None:
    record1 = make_record(run_id="pg-run-created-at")
    original_created_at = record1.created_at
    store.create_run(record1)

    record2 = make_record(run_id=record1.run_id)
    store.create_run(record2)

    got = store.get_record(record1.run_id)
    assert got is not None
    assert got.created_at == original_created_at


def test_persistence_across_reopen() -> None:
    dsn = _postgres_test_dsn()
    store1 = PostgresRunStore(dsn)
    store1.initialize()
    store1.clear()

    record = make_record(run_id="pg-run-reopen")
    store1.create_run(record)
    store1.mark_running(record.run_id)
    store1.add_step(record.run_id, make_step(step_index=1))
    store1.close()

    store2 = PostgresRunStore(dsn)
    store2.initialize()
    got_record = store2.get_record(record.run_id)
    assert got_record is not None
    assert got_record.status == "running"
    got_steps = store2.get_steps(record.run_id)
    assert got_steps is not None
    assert len(got_steps) == 1
    store2.clear()
    store2.close()


def test_get_status_returns_correct_structure(store: PostgresRunStore) -> None:
    record = make_record(run_id="pg-run-status")
    store.create_run(record)

    status = store.get_status(record.run_id)
    assert status is not None
    assert isinstance(status, RunStatusResponse)
    assert status.run_id == record.run_id
    assert status.status == "queued"
    assert status.error_type is None
    assert status.error_message is None


def test_get_nonexistent_run_returns_none(store: PostgresRunStore) -> None:
    assert store.get_record("nonexistent") is None
    assert store.get_status("nonexistent") is None
    assert store.get_steps("nonexistent") is None
    assert store.get_report("nonexistent") is None


def test_clear_empties_all_data(store: PostgresRunStore) -> None:
    record = make_record(run_id="pg-run-clear")
    store.create_run(record)
    store.add_step(record.run_id, make_step(step_index=1))

    store.clear()

    assert store.get_record(record.run_id) is None
    assert store.get_steps(record.run_id) is None
    assert store.get_report(record.run_id) is None


def test_key_screenshots_persist_in_report(store: PostgresRunStore) -> None:
    record = make_record(run_id="pg-run-screenshots")
    store.create_run(record)

    from backend.analysis.report_builder import build_run_report_without_llm

    step = make_step(step_index=1, validation_status="succeeded", detected_success=True)
    report = build_run_report_without_llm(record, [step])
    report.key_screenshots = [
        KeyScreenshot(label="成功确认", step_index=1, path="screenshots/success.png", source="after_action"),
    ]

    store.complete_run(record.run_id, report)

    got_report = store.get_report(record.run_id)
    assert got_report is not None
    assert got_report.key_screenshots == [
        KeyScreenshot(label="成功确认", step_index=1, path="screenshots/success.png", source="after_action")
    ]


def test_get_pool_closes_half_initialized_pool_on_wait_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    created_pool = None

    class FakePool:
        def __init__(self, **_kwargs) -> None:
            self.closed = False

        def wait(self) -> None:
            raise RuntimeError("boom")

        def close(self) -> None:
            self.closed = True

    def fake_connection_pool(**kwargs):
        nonlocal created_pool
        created_pool = FakePool(**kwargs)
        return created_pool

    monkeypatch.setattr("backend.stores.postgres_run_store.ConnectionPool", fake_connection_pool)
    store = PostgresRunStore("postgresql://test:test@localhost:5432/test")

    with pytest.raises(RuntimeError, match="boom"):
        store._get_pool()

    assert created_pool is not None
    assert created_pool.closed is True
    assert store._pool is None

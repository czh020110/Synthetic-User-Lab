from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.api.routes.demo_runs as demo_runs
from backend.analysis.report_builder import build_run_report
from backend.core.config import get_settings
from backend.main import app
from backend.schemas.run_schemas import (
    ActionInput,
    ExecutionResult,
    NavigateActionPayload,
    ObservedPageState,
    Persona,
    RetrievedContextItem,
    RunRecord,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
    WaitActionPayload,
)
from backend.stores import get_run_store


def _store():
    return get_run_store()


client = TestClient(app)
api_prefix = get_settings().api_prefix


def setup_function() -> None:
    _store().clear()
    demo_runs._background_tasks.clear()


def test_health_check() -> None:
    response = client.get(f"{api_prefix}/runs/demo/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_start_demo_run_returns_run_id(monkeypatch) -> None:
    async def fake_run_demo_workflow(**_kwargs):
        await asyncio.sleep(0)

    monkeypatch.setattr(demo_runs, "run_demo_workflow", fake_run_demo_workflow)

    response = client.post(
        f"{api_prefix}/runs/demo/start",
        json={
            "run_name": "demo",
            "headless": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert "run_id" in payload
    assert payload["status"] == "queued"
    async def wait_until_stopped() -> None:
        while demo_runs._background_tasks:
            await asyncio.sleep(0)

    asyncio.run(wait_until_stopped())
    status = _store().get_status(payload["run_id"])
    assert status is not None
    assert status.status in {"queued", "running", "succeeded", "failed"}


def test_background_task_failure_marks_run_failed() -> None:
    run_id = "run-background-failed"
    _store().create_run(
        RunRecord(
            run_id=run_id,
            request=RunRequest(run_name="demo"),
            persona=Persona(),
            task=Task(start_url="http://testserver/demo/index.html"),
        )
    )

    async def fail() -> None:
        raise RuntimeError("boom")

    async def run_and_wait_done_callback() -> None:
        task = asyncio.create_task(fail())
        demo_runs._track_background_task(run_id, task)
        await asyncio.gather(task, return_exceptions=True)
        await asyncio.sleep(0)

    asyncio.run(run_and_wait_done_callback())

    status = _store().get_status(run_id)
    assert status is not None
    assert status.status == "failed"
    assert status.error_message == "RuntimeError: boom"
    assert not demo_runs._background_tasks


def test_shutdown_background_tasks_cancels_pending_task() -> None:
    run_id = "run-background-cancelled"
    _store().create_run(
        RunRecord(
            run_id=run_id,
            request=RunRequest(run_name="demo"),
            persona=Persona(),
            task=Task(start_url="http://testserver/demo/index.html"),
        )
    )

    async def hang() -> None:
        await asyncio.sleep(30)

    async def cancel_and_wait() -> None:
        task = asyncio.create_task(hang())
        demo_runs._track_background_task(run_id, task)
        await demo_runs.shutdown_background_tasks()

    asyncio.run(cancel_and_wait())

    status = _store().get_status(run_id)
    assert status is not None
    assert status.status == "failed"
    assert status.error_message == "后台任务被取消。"
    assert not demo_runs._background_tasks


def _make_page_state(text: str, screenshot_path: str) -> ObservedPageState:
    return ObservedPageState(
        current_url="http://testserver/demo/index.html",
        title="demo",
        visible_text_summary=text,
        screenshot_path=screenshot_path,
    )


def test_steps_and_report_expose_recovery_branch_snapshots() -> None:
    run_id = "run-recovery-api"
    record = RunRecord(
        run_id=run_id,
        request=RunRequest(run_name="demo"),
        persona=Persona(),
        task=Task(start_url="http://testserver/demo/index.html"),
    )
    shared_retrieval_context = [
        RetrievedContextItem(
            source_type="product_knowledge",
            title="表单完成标准",
            content="页面明确显示任务完成状态、成功卡片可见且表单已隐藏时，可判定为完成。",
            source_ref="seed:product_knowledge:success_criteria",
        ),
        RetrievedContextItem(
            source_type="failure_case",
            title="页面无响应恢复",
            content="页面连续多步无变化且没有明确下一步入口时，先回到 start_url，再重新进入主流程。",
            source_ref="seed:failure_case:stuck_page",
        ),
    ]

    wait_step = StepLog(
        step_index=1,
        observed_page_state=_make_page_state("动作前页面", "screenshots/run-recovery-api/step-1-before.png"),
        decided_action=ActionInput(action="wait", payload=WaitActionPayload(duration_ms=1000), reason="等待页面恢复"),
        execution_result=ExecutionResult(action="wait", success=True, detail="wait 动作已进入等待观察节点处理。"),
        validation_result=ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="页面疑似异常卡住，准备执行受控恢复动作。",
            friction_signals=["wait_observe_abnormal_stuck", "recovery_candidate"],
        ),
        post_action_page_state=_make_page_state("等待后页面", "screenshots/run-recovery-api/step-1-after.png"),
        wait_observation_status="abnormal_stuck",
        wait_observation_reason="页面疑似异常卡住。",
        wait_observation_observations=1,
        wait_observation_elapsed_ms=30000,
        wait_observation_timeout_ms=30000,
        wait_observation_terminal_decision="abnormal_stuck",
        wait_observation_traces=[
            {
                "observation_index": 1,
                "elapsed_ms": 30000,
                "normal_wait_elapsed_ms": 0,
                "abnormal_wait_elapsed_ms": 30000,
                "decision": "abnormal_stuck",
                "reason": "页面无响应。",
                "next_wait_ms": 0,
                "screenshot_path": "screenshots/run-recovery-api/step-1-wait-1.png",
            }
        ],
        retrieval_context=shared_retrieval_context,
    )
    recovery_step = StepLog(
        step_index=2,
        observed_page_state=_make_page_state("恢复前页面", "screenshots/run-recovery-api/step-2-before.png"),
        decided_action=ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url="http://testserver/demo/index.html"),
            reason="页面卡住或偏离后，回到任务起始页重新进入主流程。",
        ),
        execution_result=ExecutionResult(action="navigate", success=True, detail="动作 navigate 执行成功。"),
        validation_result=ValidationResult(
            status="failed",
            should_stop=True,
            progress_summary="恢复后仍未完成任务。",
            friction_signals=["wait_observe_abnormal_stuck"],
            detected_error=True,
        ),
        post_action_page_state=_make_page_state("恢复后页面", "screenshots/run-recovery-api/step-2-after.png"),
        retrieval_context=shared_retrieval_context,
    )

    _store().create_run(record)
    _store().add_step(run_id, wait_step)
    _store().add_step(run_id, recovery_step)
    _store().complete_run(run_id, build_run_report(record, [wait_step, recovery_step]))

    steps_response = client.get(f"{api_prefix}/runs/demo/{run_id}/steps")
    report_response = client.get(f"{api_prefix}/runs/demo/{run_id}/report")

    assert steps_response.status_code == 200
    steps = steps_response.json()["data"]
    assert steps[0]["before_page_state"]["screenshot_path"].endswith("step-1-before.png")
    assert steps[0]["after_page_state"]["screenshot_path"].endswith("step-1-after.png")
    assert steps[0]["wait_observation_traces"][0]["screenshot_path"].endswith("step-1-wait-1.png")
    assert steps[1]["before_page_state"]["screenshot_path"].endswith("step-2-before.png")
    assert steps[1]["after_page_state"]["screenshot_path"].endswith("step-2-after.png")
    assert steps[0]["retrieval_context"] == steps[1]["retrieval_context"]
    assert {item["title"] for item in steps[0]["retrieval_context"]} == {"表单完成标准", "页面无响应恢复"}

    assert report_response.status_code == 200
    report = report_response.json()["data"]
    assert report["status"] == "failed"
    assert report["total_steps"] == 2
    assert "wait_observe_abnormal_stuck" in report["friction_signals"]
    assert report["step_details"][0]["retrieval_context"] == report["step_details"][1]["retrieval_context"]
    assert {item["title"] for item in report["step_details"][0]["retrieval_context"]} == {"表单完成标准", "页面无响应恢复"}

    assert steps[0]["decided_action"]["action"] == "wait"
    assert steps[0]["decided_action"]["payload"]["duration_ms"] == 1000
    assert steps[1]["decided_action"]["action"] == "navigate"
    assert steps[1]["decided_action"]["payload"]["url"] == "http://testserver/demo/index.html"

    assert report["step_details"][0]["action"] == "wait"
    assert report["step_details"][0]["payload"]["duration_ms"] == 1000
    assert report["step_details"][1]["action"] == "navigate"
    assert report["step_details"][1]["payload"]["url"] == "http://testserver/demo/index.html"

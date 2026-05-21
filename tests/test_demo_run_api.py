from fastapi.testclient import TestClient

from backend.analysis.report_builder import build_run_report
from backend.core.config import get_settings
from backend.main import app
from backend.schemas.run_schemas import (
    ActionInput,
    ExecutionResult,
    ObservedPageState,
    Persona,
    RunRecord,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
)
from backend.stores.in_memory_run_store import run_store

client = TestClient(app)
api_prefix = get_settings().api_prefix


def setup_function() -> None:
    run_store.clear()


def test_health_check() -> None:
    response = client.get(f"{api_prefix}/runs/demo/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_start_demo_run_returns_run_id() -> None:
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
    wait_step = StepLog(
        step_index=1,
        observed_page_state=_make_page_state("动作前页面", "screenshots/run-recovery-api/step-1-before.png"),
        decided_action=ActionInput(action="wait", target=None, value=1000, reason="等待页面恢复"),
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
    )
    recovery_step = StepLog(
        step_index=2,
        observed_page_state=_make_page_state("恢复前页面", "screenshots/run-recovery-api/step-2-before.png"),
        decided_action=ActionInput(
            action="navigate",
            target="http://testserver/demo/index.html",
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
    )

    run_store.create_run(record)
    run_store.add_step(run_id, wait_step)
    run_store.add_step(run_id, recovery_step)
    run_store.complete_run(run_id, build_run_report(record, [wait_step, recovery_step]))

    steps_response = client.get(f"{api_prefix}/runs/demo/{run_id}/steps")
    report_response = client.get(f"{api_prefix}/runs/demo/{run_id}/report")

    assert steps_response.status_code == 200
    steps = steps_response.json()["data"]
    assert steps[0]["before_page_state"]["screenshot_path"].endswith("step-1-before.png")
    assert steps[0]["after_page_state"]["screenshot_path"].endswith("step-1-after.png")
    assert steps[0]["wait_observation_traces"][0]["screenshot_path"].endswith("step-1-wait-1.png")
    assert steps[1]["decided_action"]["action"] == "navigate"
    assert steps[1]["before_page_state"]["screenshot_path"].endswith("step-2-before.png")
    assert steps[1]["after_page_state"]["screenshot_path"].endswith("step-2-after.png")

    assert report_response.status_code == 200
    report = report_response.json()["data"]
    assert report["status"] == "failed"
    assert report["total_steps"] == 2
    assert "wait_observe_abnormal_stuck" in report["friction_signals"]
    assert report["step_details"][0]["before_page_state"]["screenshot_path"].endswith("step-1-before.png")
    assert report["step_details"][0]["after_page_state"]["screenshot_path"].endswith("step-1-after.png")
    assert report["step_details"][0]["wait_observation_traces"][0]["screenshot_path"].endswith("step-1-wait-1.png")

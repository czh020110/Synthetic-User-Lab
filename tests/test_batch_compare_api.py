from __future__ import annotations

"""批量 run 与对比报告 API 及聚合函数测试。"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.analysis.compare_report import (
    RunNotFoundError,
    RunNotReadyError,
    TaskMismatchError,
    build_compare_report,
)
from backend.main import app
from backend.schemas.persona_schemas import Persona
from backend.schemas.run_schemas import RunRecord, RunReport, RunRequest
from backend.schemas.task_schemas import Task
from backend.stores import get_entity_store, get_run_store

client = TestClient(app)


def setup_function():
    """每个测试前清空 store。"""
    get_entity_store().clear()
    get_run_store().clear()


def _create_personas_and_task(count: int = 2):
    """创建 count 个 persona 和 1 个 task，返回 (persona_ids, task_id)。"""
    entity_store = get_entity_store()
    personas = []
    for i in range(count):
        persona = Persona(name=f"用户{i}", skill_level="intermediate")
        entity_store.create_persona(persona)
        personas.append(persona)
    task = Task(name="对比任务", start_url="http://example.com", max_steps=5)
    entity_store.create_task(task)
    return [p.id for p in personas], task.id


def _make_report(record, *, success=True, conclusion="keep", total_steps=3,
                 friction_signals=None, summary="ok"):
    return RunReport(
        run_id=record.run_id,
        status="succeeded" if success else "failed",
        summary=summary,
        success=success,
        conclusion=conclusion,
        persona=record.persona,
        task=record.task,
        total_steps=total_steps,
        friction_signals=friction_signals or [],
    )


def _create_completed_run(persona, task, **overrides) -> str:
    """直接通过 store 构造一个已完成的 run，返回 run_id。"""
    run_id = str(uuid4())
    record = RunRecord(run_id=run_id, request=RunRequest(run_name="test"), persona=persona, task=task)
    store = get_run_store()
    store.create_run(record)
    report = _make_report(record, **overrides)
    store.complete_run(run_id, report)
    return run_id


# ============================ batch run API ============================ #


def test_batch_run_success():
    persona_ids, task_id = _create_personas_and_task(count=2)
    with patch("backend.api.routes.runs.run_formal_workflow", new_callable=AsyncMock):
        resp = client.post("/api/v1/runs/batch", json={
            "task_id": task_id,
            "persona_ids": persona_ids,
        })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["task_id"] == task_id
    assert len(data["run_ids"]) == 2
    store = get_run_store()
    for rid in data["run_ids"]:
        status = store.get_status(rid)
        assert status is not None
        assert status.status in {"queued", "running"}


def test_batch_run_empty_persona_ids():
    _, task_id = _create_personas_and_task()
    resp = client.post("/api/v1/runs/batch", json={
        "task_id": task_id,
        "persona_ids": [],
    })
    assert resp.status_code == 422


def test_batch_run_task_not_found():
    persona_ids, _ = _create_personas_and_task()
    resp = client.post("/api/v1/runs/batch", json={
        "task_id": "nonexistent",
        "persona_ids": persona_ids,
    })
    assert resp.status_code == 404
    assert "Task" in resp.json()["detail"]


def test_batch_run_persona_not_found():
    persona_ids, task_id = _create_personas_and_task()
    resp = client.post("/api/v1/runs/batch", json={
        "task_id": task_id,
        "persona_ids": [persona_ids[0], "nonexistent"],
    })
    assert resp.status_code == 404
    assert "Persona" in resp.json()["detail"]


# ============================ compare API ============================ #


def test_compare_success():
    persona_ids, task_id = _create_personas_and_task(count=3)
    entity_store = get_entity_store()
    task = entity_store.get_task(task_id)
    personas = [entity_store.get_persona(pid) for pid in persona_ids]

    rid_keep = _create_completed_run(personas[0], task, success=True, conclusion="keep", total_steps=3)
    rid_opt = _create_completed_run(personas[1], task, success=True, conclusion="optimize", total_steps=5, friction_signals=["stuck_page"])
    rid_fix = _create_completed_run(personas[2], task, success=False, conclusion="fix", total_steps=7, summary="失败")

    resp = client.post("/api/v1/runs/compare", json={"run_ids": [rid_keep, rid_opt, rid_fix]})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["run_count"] == 3
    assert data["success_count"] == 2
    assert data["conclusion_distribution"] == {"keep": 1, "optimize": 1, "fix": 1}
    assert data["avg_steps"] == 5.0
    assert data["total_friction_signals"] == 1
    assert len(data["items"]) == 3
    assert data["items"][0]["run_id"] == rid_keep
    assert data["items"][0]["success"] is True
    assert data["items"][2]["success"] is False
    assert data["comparison_summary"]


def test_compare_run_not_found():
    persona_ids, task_id = _create_personas_and_task(count=2)
    entity_store = get_entity_store()
    rid = _create_completed_run(entity_store.get_persona(persona_ids[0]), entity_store.get_task(task_id))
    resp = client.post("/api/v1/runs/compare", json={"run_ids": [rid, "nonexistent"]})
    assert resp.status_code == 404
    assert "Run not found" in resp.json()["detail"]


def test_compare_run_not_ready():
    """未完成(queued/running)的 run 返回 409。"""
    persona_ids, task_id = _create_personas_and_task(count=2)
    with patch("backend.api.routes.runs.run_formal_workflow", new_callable=AsyncMock):
        resp1 = client.post("/api/v1/runs/start", json={"persona_id": persona_ids[0], "task_id": task_id})
        resp2 = client.post("/api/v1/runs/start", json={"persona_id": persona_ids[1], "task_id": task_id})
    rid1 = resp1.json()["data"]["run_id"]
    rid2 = resp2.json()["data"]["run_id"]
    resp = client.post("/api/v1/runs/compare", json={"run_ids": [rid1, rid2]})
    assert resp.status_code == 409
    assert "not finished" in resp.json()["detail"]


def test_compare_task_mismatch():
    """不同 task 的 run 返回 400。"""
    entity_store = get_entity_store()
    p1 = Persona(name="u1", skill_level="intermediate"); entity_store.create_persona(p1)
    p2 = Persona(name="u2", skill_level="intermediate"); entity_store.create_persona(p2)
    t1 = Task(name="t1", start_url="http://example.com", max_steps=5); entity_store.create_task(t1)
    t2 = Task(name="t2", start_url="http://example.com", max_steps=5); entity_store.create_task(t2)
    rid1 = _create_completed_run(p1, t1)
    rid2 = _create_completed_run(p2, t2)
    resp = client.post("/api/v1/runs/compare", json={"run_ids": [rid1, rid2]})
    assert resp.status_code == 400
    assert "task" in resp.json()["detail"]


def test_compare_too_few_run_ids():
    persona_ids, task_id = _create_personas_and_task()
    entity_store = get_entity_store()
    rid = _create_completed_run(entity_store.get_persona(persona_ids[0]), entity_store.get_task(task_id))
    resp = client.post("/api/v1/runs/compare", json={"run_ids": [rid]})
    assert resp.status_code == 422


# ============================ build_compare_report 纯函数 ============================ #


def test_build_compare_report_failed_run_without_report():
    """fail_run 路径下无 report 的 run 仍可聚合为失败条目。"""
    entity_store = get_entity_store()
    p1 = Persona(name="u1", skill_level="intermediate"); entity_store.create_persona(p1)
    p2 = Persona(name="u2", skill_level="intermediate"); entity_store.create_persona(p2)
    task = Task(name="t", start_url="http://example.com", max_steps=5); entity_store.create_task(task)
    rid_ok = _create_completed_run(p1, task, success=True, conclusion="keep", total_steps=4)

    rid_fail = str(uuid4())
    record = RunRecord(run_id=rid_fail, request=RunRequest(run_name="test"), persona=p2, task=task)
    store = get_run_store()
    store.create_run(record)
    store.fail_run(rid_fail, "模型调用失败")

    report = build_compare_report([rid_ok, rid_fail], store)
    assert report.run_count == 2
    assert report.success_count == 1
    assert report.conclusion_distribution == {"keep": 1, "optimize": 0, "fix": 1}
    fail_item = next(it for it in report.items if it.run_id == rid_fail)
    assert fail_item.success is False
    assert fail_item.conclusion == "fix"
    assert fail_item.total_steps == 0
    assert "模型调用失败" in fail_item.summary


def test_build_compare_report_run_not_found():
    entity_store = get_entity_store()
    p1 = Persona(name="u1", skill_level="intermediate"); entity_store.create_persona(p1)
    task = Task(name="t", start_url="http://example.com", max_steps=5); entity_store.create_task(task)
    rid = _create_completed_run(p1, task)
    try:
        build_compare_report([rid, "ghost"], get_run_store())
        assert False, "应抛 RunNotFoundError"
    except RunNotFoundError:
        pass


def test_build_compare_report_not_ready():
    entity_store = get_entity_store()
    p1 = Persona(name="u1", skill_level="intermediate"); entity_store.create_persona(p1)
    task = Task(name="t", start_url="http://example.com", max_steps=5); entity_store.create_task(task)
    rid = _create_completed_run(p1, task)
    rid_running = str(uuid4())
    record = RunRecord(run_id=rid_running, request=RunRequest(run_name="test"), persona=p1, task=task)
    store = get_run_store()
    store.create_run(record)
    store.mark_running(rid_running)
    try:
        build_compare_report([rid, rid_running], store)
        assert False, "应抛 RunNotReadyError"
    except RunNotReadyError:
        pass


def test_build_compare_report_task_mismatch():
    entity_store = get_entity_store()
    p1 = Persona(name="u1", skill_level="intermediate"); entity_store.create_persona(p1)
    t1 = Task(name="t1", start_url="http://example.com", max_steps=5); entity_store.create_task(t1)
    t2 = Task(name="t2", start_url="http://example.com", max_steps=5); entity_store.create_task(t2)
    rid1 = _create_completed_run(p1, t1)
    rid2 = _create_completed_run(p1, t2)
    try:
        build_compare_report([rid1, rid2], get_run_store())
        assert False, "应抛 TaskMismatchError"
    except TaskMismatchError:
        pass

from __future__ import annotations

from pathlib import Path
from typing import get_args
from uuid import uuid4

from backend.analysis.compare_report import build_compare_report
from backend.analysis.report_builder import build_run_report_without_llm
from backend.fixtures.friction_experiments import (
    KNOWN_EXPERIMENT_FRICTION_SIGNALS,
    FrictionExperiment,
    get_friction_experiment,
    get_friction_experiments,
)
from backend.fixtures.mvp_samples import get_mvp_personas, get_mvp_tasks
from backend.schemas.persona_schemas import Persona
from backend.schemas.run_schemas import ReportConclusion, RunRecord, RunRequest
from backend.schemas.task_schemas import Task
from backend.stores import get_run_store

_PRODUCT_HTML = Path("backend/fixtures/test_site/product.html").read_text(encoding="utf-8")
_CHECKOUT_HTML = Path("backend/fixtures/test_site/checkout.html").read_text(encoding="utf-8")
_SUCCESS_HTML = Path("backend/fixtures/test_site/success.html").read_text(encoding="utf-8")


def _persona_by_name(name: str) -> Persona:
    for persona in get_mvp_personas():
        if persona.name == name:
            return Persona(**persona.model_dump())
    raise AssertionError(f"persona not found: {name}")


def _task_by_name(name: str) -> Task:
    for task in get_mvp_tasks():
        if task.name == name:
            return Task(**task.model_dump())
    raise AssertionError(f"task not found: {name}")


def _build_report(experiment: FrictionExperiment):
    record = RunRecord(
        run_id=str(uuid4()),
        request=RunRequest(run_name=experiment.experiment_id),
        persona=_persona_by_name(experiment.persona_name),
        task=_task_by_name(experiment.task_name),
    )
    return build_run_report_without_llm(record, experiment.build_steps())


def _store_completed_experiment(experiment: FrictionExperiment, *, task: Task | None = None) -> str:
    store = get_run_store()
    record = RunRecord(
        run_id=str(uuid4()),
        request=RunRequest(run_name=experiment.experiment_id),
        persona=_persona_by_name(experiment.persona_name),
        task=task or _task_by_name(experiment.task_name),
    )
    store.create_run(record)
    steps = experiment.build_steps()
    for step in steps:
        store.add_step(record.run_id, step)
    report = build_run_report_without_llm(record, steps)
    store.complete_run(record.run_id, report)
    return record.run_id


def _html_for_url(url: str) -> str:
    if url.endswith("/product.html"):
        return _PRODUCT_HTML
    if url.endswith("/checkout.html"):
        return _CHECKOUT_HTML
    if url.endswith("/success.html"):
        return _SUCCESS_HTML
    raise AssertionError(f"unexpected url: {url}")


def _selector_token(selector: str) -> str:
    if selector.startswith("#"):
        return f'id="{selector[1:]}"'
    if selector.startswith("[data-testid=\"") and selector.endswith("\"]"):
        return f'data-testid="{selector.removeprefix("[data-testid=\"").removesuffix("\"]")}"'
    return selector


def test_friction_experiments_are_unique_and_complete():
    experiments = get_friction_experiments()
    ids = [experiment.experiment_id for experiment in experiments]
    assert len(experiments) == 4
    assert len(ids) == len(set(ids))
    assert {"E-001", "E-002", "E-003", "E-004"} == set(ids)


def test_friction_experiments_reference_mvp_samples():
    persona_names = {persona.name for persona in get_mvp_personas()}
    task_names = {task.name for task in get_mvp_tasks()}

    for experiment in get_friction_experiments():
        assert experiment.persona_name in persona_names
        assert experiment.task_name in task_names


def test_friction_experiment_expectations_are_valid():
    conclusions = set(get_args(ReportConclusion))

    for experiment in get_friction_experiments():
        assert experiment.expected_conclusion in conclusions
        assert set(experiment.expected_friction_signals).issubset(KNOWN_EXPERIMENT_FRICTION_SIGNALS)


def test_friction_experiment_selectors_exist_in_real_pages():
    for experiment in get_friction_experiments():
        for step in experiment.scripted_steps:
            selector = step.payload.get("selector")
            if not isinstance(selector, str):
                continue
            assert _selector_token(selector) in _html_for_url(step.before_url)


def test_friction_experiment_step_urls_are_contiguous():
    for experiment in get_friction_experiments():
        for previous, current in zip(experiment.scripted_steps, experiment.scripted_steps[1:]):
            expected_before_url = previous.after_url or previous.before_url
            assert current.before_url == expected_before_url


def test_newbie_checkout_produces_more_friction_than_expert_checkout():
    newbie_report = _build_report(get_friction_experiment("E-001"))
    expert_report = _build_report(get_friction_experiment("E-002"))

    assert newbie_report.conclusion == "fix"
    assert expert_report.conclusion == "keep"
    assert len(newbie_report.friction_signals) > len(expert_report.friction_signals)
    assert {"page_error", "recovery_candidate", "stuck_page"}.issubset(newbie_report.friction_signals)
    assert expert_report.friction_signals == []


def test_coupon_experiments_produce_expected_friction():
    elderly_report = _build_report(get_friction_experiment("E-003"))
    newbie_report = _build_report(get_friction_experiment("E-004"))

    assert elderly_report.success is True
    assert elderly_report.conclusion == "optimize"
    assert {"page_error", "recovery_candidate"}.issubset(elderly_report.friction_signals)

    assert newbie_report.success is False
    assert newbie_report.conclusion == "fix"
    assert {"page_error", "recovery_candidate"}.issubset(newbie_report.friction_signals)


def test_checkout_compare_report_surfaces_persona_friction_contrast():
    checkout_task = _task_by_name("填写结算表单完成支付")
    checkout_run_ids = [
        _store_completed_experiment(get_friction_experiment("E-001"), task=checkout_task),
        _store_completed_experiment(get_friction_experiment("E-002"), task=checkout_task),
    ]

    report = build_compare_report(checkout_run_ids, get_run_store())
    items_by_persona = {item.persona.name: item for item in report.items}

    assert report.run_count == 2
    assert report.success_count == 1
    assert report.conclusion_distribution["fix"] == 1
    assert report.conclusion_distribution["keep"] == 1
    assert items_by_persona["新手用户"].friction_signal_count > items_by_persona["专家用户"].friction_signal_count
    assert items_by_persona["专家用户"].friction_signal_count == 0


def test_coupon_compare_report_surfaces_persona_outcome_gap():
    coupon_task = _task_by_name("使用优惠券购买商品")
    coupon_run_ids = [
        _store_completed_experiment(get_friction_experiment("E-003"), task=coupon_task),
        _store_completed_experiment(get_friction_experiment("E-004"), task=coupon_task),
    ]

    report = build_compare_report(coupon_run_ids, get_run_store())
    items_by_persona = {item.persona.name: item for item in report.items}

    assert report.run_count == 2
    assert report.success_count == 1
    assert report.conclusion_distribution["optimize"] == 1
    assert report.conclusion_distribution["fix"] == 1
    assert items_by_persona["老年用户"].success is True
    assert items_by_persona["新手用户"].success is False
    assert items_by_persona["老年用户"].total_steps > items_by_persona["新手用户"].total_steps

#!/usr/bin/env python3
"""MVP 端到端验收脚本。

覆盖 S-005 两条验收路径：
  1. Demo Run 闭环：POST /runs/demo/start → status → steps → report → markdown
  2. 正式 Run 闭环：seed MVP 样例 → POST /runs/start → status → steps → report → markdown
并附带真实验证动作安全护栏（S-005 安全边界目标）。

设计说明：
  真实 run workflow 依赖 LLM + Playwright，无法在 CI 稳定复跑。本脚本在 workflow
  入口注入受控剧本（写入真实 StepLog 并调用 run_store.complete_run），使 API → store
  → 报告 → Markdown 查询链路得到端到端覆盖，同时保留可解释的步骤证据。安全护栏
  不依赖 LLM，直接调用 is_destructive_action 真实验证。

使用方式：
    python scripts/acceptance_check.py
    python scripts/acceptance_check.py --keep-reports  # 保留历史验收报告
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient

from backend.analysis.compare_report import build_compare_report
from backend.analysis.report_builder import build_run_report_without_llm
from backend.execution.action_guard import is_destructive_action
from backend.fixtures.friction_experiments import FrictionExperiment, get_friction_experiments
from backend.fixtures.mvp_samples import get_mvp_personas, get_mvp_tasks
from backend.main import app
from backend.retrieval import build_retrieval_context, retrieve_failure_cases
from backend.schemas.knowledge_schemas import KnowledgeItemCreate
from backend.schemas.persona_schemas import Persona
from backend.schemas.run_schemas import (
    AbandonPayload,
    ActionInput,
    ClickActionPayload,
    ExecutionResult,
    FillActionPayload,
    NavigateActionPayload,
    ObservedPageState,
    RetrievedContextItem,
    RunRecord,
    RunReport,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
)
from backend.stores import get_entity_store, get_run_store

client = TestClient(app)
REPORT_DIR = project_root / "acceptance_reports"


# ============================ 验收结果收集 ============================ #


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class AcceptanceReport:
    started_at: str
    finished_at: str = ""
    results: list[CheckResult] = field(default_factory=list)
    demo_run_id: str | None = None
    formal_run_id: str | None = None
    demo_markdown: str | None = None
    formal_markdown: str | None = None

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return self.total - self.passed_count

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0


def record(report: AcceptanceReport, name: str, condition: bool, detail: str = "") -> None:
    report.results.append(CheckResult(name=name, passed=bool(condition), detail=detail))
    flag = "PASS" if condition else "FAIL"
    print(f"  [{flag}] {name}{(' — ' + detail) if detail and not condition else ''}")


# ============================ 受控 workflow 剧本 ============================ #
# 用确定性步骤代替真实 LLM 决策，写入真实 StepLog 并完成 run，
# 使 API → store → 报告 → Markdown 查询链路得到端到端覆盖。

_DEMO_START_URL = "http://testserver/demo/index.html"


def _make_page_state(text: str, screenshot: str) -> ObservedPageState:
    return ObservedPageState(
        current_url=_DEMO_START_URL,
        title="demo 动作验证",
        visible_text_summary=text,
        screenshot_path=screenshot,
    )


def _build_scripted_steps(run_id: str, success: bool) -> list[StepLog]:
    """构造两步确定性步骤证据：navigate 进入 → click 完成（成功）或 abandon（失败）。"""

    retrieval_context = [
        RetrievedContextItem(
            source_type="product_knowledge",
            title="任务完成标准",
            content="页面显示成功卡片且计数器大于 0 时判定为完成。",
            source_ref="acceptance:success_criteria",
        ),
    ]
    step1 = StepLog(
        step_index=1,
        observed_page_state=_make_page_state("起始页面，计数器为 0", f"screenshots/{run_id}/step-1-before.png"),
        decided_action=ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=_DEMO_START_URL),
            reason="进入任务起始页",
        ),
        execution_result=ExecutionResult(action="navigate", success=True, detail="动作 navigate 执行成功。"),
        validation_result=ValidationResult(
            status="running",
            should_stop=False,
            progress_summary="已进入起始页面，准备执行核心动作。",
        ),
        post_action_page_state=_make_page_state("已进入起始页", f"screenshots/{run_id}/step-1-after.png"),
        retrieval_context=retrieval_context,
    )
    if success:
        step2 = StepLog(
            step_index=2,
            observed_page_state=_make_page_state("点击前计数器为 0", f"screenshots/{run_id}/step-2-before.png"),
            decided_action=ActionInput(
                action="click",
                payload=ClickActionPayload(
                    selector="#btn-counter-increment"
                ),
                reason="点击 +1 按钮增加计数器",
            ),
            execution_result=ExecutionResult(action="click", success=True, detail="动作 click 执行成功。"),
            validation_result=ValidationResult(
                status="succeeded",
                should_stop=True,
                progress_summary="计数器增加且成功卡片可见，任务完成。",
                detected_success=True,
            ),
            post_action_page_state=_make_page_state("成功卡片可见，计数器为 1", f"screenshots/{run_id}/step-2-after.png"),
            retrieval_context=retrieval_context,
        )
    else:
        step2 = StepLog(
            step_index=2,
            observed_page_state=_make_page_state("点击前计数器为 0", f"screenshots/{run_id}/step-2-before.png"),
            decided_action=ActionInput(
                action="abandon",
                payload=AbandonPayload(
                    reason="找不到可用入口"
                ),
                reason="无法定位可用按钮",
            ),
            execution_result=ExecutionResult(action="abandon", success=True, detail="动作 abandon 执行成功。"),
            validation_result=ValidationResult(
                status="failed",
                should_stop=True,
                progress_summary="未找到可用入口，任务被放弃。",
                detected_error=True,
            ),
            post_action_page_state=_make_page_state("放弃任务", f"screenshots/{run_id}/step-2-after.png"),
            retrieval_context=retrieval_context,
        )
    return [step1, step2]


async def _scripted_demo_workflow(run_id: str, **_kwargs) -> None:
    """受控 demo workflow：写入真实步骤证据并完成 run。"""

    from backend.analysis.report_builder import build_run_report_async

    run_store = get_run_store()
    record = run_store.get_record(run_id)
    if record is None:
        record = RunRecord(
            run_id=run_id,
            request=RunRequest(run_name="acceptance-demo"),
            persona=Persona(name="验收 demo persona"),
            task=Task(start_url=_DEMO_START_URL),
        )
        run_store.create_run(record)
    run_store.mark_running(run_id)
    steps = _build_scripted_steps(run_id, success=True)
    for step in steps:
        run_store.add_step(run_id, step)
    report = await build_run_report_async(record, steps)
    run_store.complete_run(run_id, report)


async def _scripted_formal_workflow(run_id: str, **_kwargs) -> None:
    """受控 formal workflow：写入真实步骤证据并完成 run。"""

    from backend.analysis.report_builder import build_run_report_async

    run_store = get_run_store()
    record = run_store.get_record(run_id)
    if record is None:
        raise ValueError("formal run record must be created by API before workflow")
    run_store.mark_running(run_id)
    steps = _build_scripted_steps(run_id, success=True)
    for step in steps:
        run_store.add_step(run_id, step)
    report = await build_run_report_async(record, steps)
    run_store.complete_run(run_id, report)


# ============================ 验收步骤 ============================ #


def _reset_stores() -> None:
    """清空 store，保证验收可重复运行。"""

    get_entity_store().clear()
    get_run_store().clear()


def _seed_mvp_samples() -> tuple[str, str]:
    """通过 API 创建 MVP 样例 persona/task，返回 (persona_id, task_id)。"""

    persona_payload = get_mvp_personas()[0].model_dump()
    task_payload = get_mvp_tasks()[0].model_dump()
    persona_resp = client.post("/api/v1/personas/", json=persona_payload)
    assert persona_resp.status_code == 200, persona_resp.text
    task_resp = client.post("/api/v1/tasks/", json=task_payload)
    assert task_resp.status_code == 200, task_resp.text
    return persona_resp.json()["data"]["id"], task_resp.json()["data"]["id"]


def check_demo_run_path(report: AcceptanceReport) -> None:
    """验收路径 1：Demo Run 闭环。"""

    print("\n[路径 1] Demo Run 端到端闭环")
    with patch("backend.api.routes.demo_runs.run_demo_workflow", new=_scripted_demo_workflow):
        start_resp = client.post("/api/v1/runs/demo/start", json={"run_name": "acceptance-demo", "headless": True})
    record(report, "POST /runs/demo/start 返回 200 + run_id", start_resp.status_code == 200)
    start_data = start_resp.json().get("data", {})
    run_id = start_data.get("run_id")
    report.demo_run_id = run_id
    record(report, "启动状态为 queued", start_data.get("status") == "queued", f"status={start_data.get('status')}")

    if run_id is None:
        record(report, "获取 demo run_id", False, "启动响应缺失 run_id")
        return

    # 受控 workflow 在后台 task 中执行；TestClient 同步上下文需等待其完成
    _drain_demo_background_tasks()

    status_resp = client.get(f"/api/v1/runs/demo/{run_id}")
    status_data = status_resp.json().get("data", {})
    record(report, "GET status 返回 200", status_resp.status_code == 200)
    record(report, "最终状态为 succeeded", status_data.get("status") == "succeeded", f"status={status_data.get('status')}")

    steps_resp = client.get(f"/api/v1/runs/demo/{run_id}/steps")
    steps_data = steps_resp.json().get("data", [])
    record(report, "GET steps 返回 200", steps_resp.status_code == 200)
    record(report, "steps 包含 2 条步骤日志", len(steps_data) == 2, f"len={len(steps_data)}")
    if steps_data:
        record(
            report,
            "步骤日志含动作前/后截图路径",
            steps_data[0]["before_page_state"]["screenshot_path"].endswith("step-1-before.png")
            and steps_data[1]["after_page_state"]["screenshot_path"].endswith("step-2-after.png"),
        )

    report_resp = client.get(f"/api/v1/runs/demo/{run_id}/report")
    report_data = report_resp.json().get("data", {})
    record(report, "GET report 返回 200", report_resp.status_code == 200)
    record(report, "报告 conclusion=keep", report_data.get("conclusion") == "keep", f"conclusion={report_data.get('conclusion')}")
    record(report, "报告 total_steps=2", report_data.get("total_steps") == 2, f"total_steps={report_data.get('total_steps')}")
    record(report, "报告含结构化事实 structured_facts", bool(report_data.get("structured_facts")))

    md_resp = client.get(f"/api/v1/runs/demo/{run_id}/report/markdown")
    md_text = md_resp.json().get("data", {}).get("markdown", "")
    report.demo_markdown = md_text
    record(report, "GET report/markdown 返回 200", md_resp.status_code == 200)
    record(report, "Markdown 含执行摘要与步骤明细", "## 执行摘要" in md_text and "## 步骤明细" in md_text)


def check_formal_run_path(report: AcceptanceReport) -> None:
    """验收路径 2：正式 Run 闭环（seed MVP 样例 → 启动 → 查询）。"""

    print("\n[路径 2] 正式 Run 端到端闭环")
    persona_id, task_id = _seed_mvp_samples()
    record(report, "通过 API 创建 MVP persona/task", bool(persona_id and task_id))

    with patch("backend.api.routes.runs.run_formal_workflow", new=_scripted_formal_workflow):
        start_resp = client.post(
            "/api/v1/runs/start",
            json={"persona_id": persona_id, "task_id": task_id, "run_name": "acceptance-formal"},
        )
    record(report, "POST /runs/start 返回 200 + run_id", start_resp.status_code == 200, start_resp.text)
    start_data = start_resp.json().get("data", {})
    run_id = start_data.get("run_id")
    report.formal_run_id = run_id

    if run_id is None:
        record(report, "获取 formal run_id", False, "启动响应缺失 run_id")
        return

    _drain_formal_background_tasks()

    status_resp = client.get(f"/api/v1/runs/{run_id}")
    status_data = status_resp.json().get("data", {})
    record(report, "GET status 返回 200 + succeeded", status_resp.status_code == 200 and status_data.get("status") == "succeeded")

    steps_resp = client.get(f"/api/v1/runs/{run_id}/steps")
    record(report, "GET steps 返回 200", steps_resp.status_code == 200)
    record(report, "steps 含 2 条证据", len(steps_resp.json().get("data", [])) == 2)

    report_resp = client.get(f"/api/v1/runs/{run_id}/report")
    report_data = report_resp.json().get("data", {})
    record(report, "GET report 返回 200", report_resp.status_code == 200)
    record(report, "报告绑定正式 persona/task", report_data.get("persona", {}).get("name") == "新手用户")
    record(report, "报告 conclusion=keep", report_data.get("conclusion") == "keep")

    md_resp = client.get(f"/api/v1/runs/{run_id}/report/markdown")
    report.formal_markdown = md_resp.json().get("data", {}).get("markdown", "")
    record(report, "GET report/markdown 返回 200", md_resp.status_code == 200)

    list_resp = client.get("/api/v1/runs/")
    record(report, "GET /runs 列表返回 200", list_resp.status_code == 200)
    record(report, "列表包含本次 formal run", any(r.get("run_id") == run_id for r in list_resp.json().get("data", [])))


def check_error_branches(report: AcceptanceReport) -> None:
    """验收错误分支：404 不存在 / 409 报告未就绪。"""

    print("\n[路径 3] 错误分支与友好提示")
    not_found = client.get("/api/v1/runs/nonexistent-run")
    record(report, "查询不存在 run 返回 404", not_found.status_code == 404, f"code={not_found.status_code}")

    # 创建一个 queued 但后台 workflow 不构建报告的 run，验证 409。
    # 与 tests/test_formal_run_api.py::test_get_run_report_not_ready 一致：workflow 立即返回，
    # 既不 complete_run 也不构建报告，因此 run 处于未完成态、报告缺失 → 409。
    async def _noop_workflow(run_id: str, **_kwargs) -> None:
        return None

    entity_store = get_entity_store()
    persona = Persona(name="错误分支 persona")
    entity_store.create_persona(persona)
    task = Task(start_url="http://example.com", max_steps=5)
    entity_store.create_task(task)
    with patch("backend.api.routes.runs.run_formal_workflow", new=_noop_workflow):
        start_resp = client.post("/api/v1/runs/start", json={"persona_id": persona.id, "task_id": task.id})
    run_id = start_resp.json()["data"]["run_id"]
    _drain_formal_background_tasks()

    early_report = client.get(f"/api/v1/runs/{run_id}/report")
    record(report, "run 报告未就绪时返回 409", early_report.status_code == 409, f"code={early_report.status_code}")


def check_knowledge_retrieval(report: AcceptanceReport) -> None:
    """验收路径 5：知识检索接入 knowledge_items。"""

    print("\n[路径 5] 知识检索接入 knowledge_items")
    entity_store = get_entity_store()
    persona = Persona(name="验收测试用户", description="测试用户", skill_level="newbie")
    task = Task(name="测试任务", description="测试注册流程", start_url="http://testserver")

    # === 空库兜底：不设知识条目，build_retrieval_context 应回退硬编码种子 ===
    items = build_retrieval_context(persona, task, entity_store=entity_store)
    record(report, "空库时 build_retrieval_context 不报错并返回结果", len(items) > 0)

    friction_empty = retrieve_failure_cases([], [])
    record(report, "无摩擦信号时 retrieve_failure_cases 返回空", len(friction_empty) == 0)

    friction_fallback = retrieve_failure_cases(["stuck_page"], [], entity_store=entity_store)
    record(report, "空库时 retrieve_failure_cases 回退到硬编码种子", len(friction_fallback) > 0)

    # === 录入知识条目后验证命中 ===
    product_item = KnowledgeItemCreate(
        source_type="product_knowledge",
        title="验收测试：注册完成条件",
        content="用户注册成功后应显示欢迎卡片且已填充用户名。",
        keywords=["注册", "欢迎卡片", "用户名", "完成"],
        source_ref="acceptance:test:register",
    )
    product_resp = client.post("/api/v1/knowledge/", json=product_item.model_dump())
    record(report, "POST /knowledge (product_knowledge) 返回 200", product_resp.status_code == 200)

    failure_item = KnowledgeItemCreate(
        source_type="failure_case",
        title="验收测试：页面无响应",
        content="页面卡住时先尝试按 Escape，再回起始页。",
        keywords=["卡住", "无响应", "Escape", "起始页"],
        source_ref="acceptance:test:stuck",
    )
    failure_resp = client.post("/api/v1/knowledge/", json=failure_item.model_dump())
    record(report, "POST /knowledge (failure_case) 返回 200", failure_resp.status_code == 200)

    # 验证 product_knowledge 命中
    product_items = build_retrieval_context(persona, task, entity_store=entity_store)
    product_hit = any("acceptance:test:register" in item.source_ref for item in product_items)
    record(report, "build_retrieval_context 命中验收产品知识条目", product_hit)

    # 验证 failure_case 命中
    failure_items = retrieve_failure_cases(["卡住"], [], entity_store=entity_store)
    failure_hit = any("acceptance:test:stuck" in item.source_ref for item in failure_items)
    record(report, "retrieve_failure_cases 命中验收失败案例条目", failure_hit)

    # source_type 过滤
    only_knowledge = build_retrieval_context(persona, task, entity_store=entity_store, limit_per_type=10)
    only_product = [i for i in only_knowledge if i.source_type == "product_knowledge"]
    only_failure = [i for i in only_knowledge if i.source_type == "failure_case"]
    record(report, "product_knowledge 与 failure_case 均在 retrieval_context 中分别出现",
           len(only_product) > 0 and len(only_failure) > 0)

    # 创建后的 failure_case 也在 retrieval_context 中出现（build_retrieval_context 通吃两种 source_type）
    record(report, "failure_case 条目出现在 build_retrieval_context 返回值中",
           any(i.source_type == "failure_case" and "acceptance:test:stuck" in i.source_ref for i in only_knowledge))

    print("\n[路径 4] 动作安全护栏")
    task = Task(start_url="https://example.com", destructive_action_allowed=False)

    # 高风险点击应被阻断
    click_blocked, _ = is_destructive_action(
        ActionInput(action="click", payload=ClickActionPayload(selector="button:has-text('Delete Account')")),
        task,
    )
    record(report, "高风险点击被护栏阻断", click_blocked)

    # 敏感字段填写应被阻断
    fill_blocked, _ = is_destructive_action(
        ActionInput(action="fill", payload=FillActionPayload(selector="input[name='password']", value="x")),
        task,
    )
    record(report, "敏感字段填写被护栏阻断", fill_blocked)

    # 非白名单域名导航应被阻断
    nav_blocked, _ = is_destructive_action(
        ActionInput(action="navigate", payload=NavigateActionPayload(url="https://malicious.com")),
        task,
    )
    record(report, "非白名单域名导航被阻断", nav_blocked)

    # 安全动作不应被误伤
    safe_ok, _ = is_destructive_action(
        ActionInput(action="click", payload=ClickActionPayload(selector="#btn-submit-form")),
        task,
    )
    record(report, "普通提交按钮不被误伤", not safe_ok)

    # destructive_action_allowed=True 时放行
    task_allowed = Task(start_url="https://example.com", destructive_action_allowed=True)
    allowed_ok, _ = is_destructive_action(
        ActionInput(action="click", payload=ClickActionPayload(selector="button:has-text('Delete Account')")),
        task_allowed,
    )
    record(report, "destructive_action_allowed=True 时放行", not allowed_ok)


# ============================ 后台任务排空 ============================ #


def _drain_demo_background_tasks() -> None:
    import backend.api.routes.demo_runs as demo_runs

    async def _wait() -> None:
        while demo_runs._background_tasks:
            await asyncio.sleep(0)

    asyncio.run(_wait())


def _drain_formal_background_tasks() -> None:
    import backend.api.routes.runs as runs

    async def _wait() -> None:
        while runs._background_tasks:
            await asyncio.sleep(0)

    asyncio.run(_wait())


# ============================ 测试站点验收（S-008） ============================ #


def check_test_site(report: AcceptanceReport) -> None:
    """验收路径：自托管测试产品站点 ShopLab 可访问、含 UX 摩擦埋点，且 MVP 样例指向该站点。

    不依赖 LLM/Playwright，仅校验站点页面结构与 MVP 样例 start_url 指向。
    """

    print("\n[路径 5] 测试产品站点 ShopLab 可访问性与摩擦埋点")
    # 每个页面只请求一次，status 与内容复用同一响应，避免重复 HTTP 往返。
    page_contents: dict[str, str] = {}
    for page in ["/site/", "/site/index.html", "/site/product.html", "/site/checkout.html", "/site/success.html"]:
        resp = client.get(page)
        record(report, f"测试站点 {page} 可访问", resp.status_code == 200, f"status={resp.status_code}")
        if resp.status_code == 200:
            page_contents[page] = resp.text

    index = page_contents.get("/site/index.html", "")
    record(report, "首页含商品详情入口", "查看详情" in index and "product.html" in index)

    product = page_contents.get("/site/product.html", "")
    record(
        report,
        "商品页埋入摩擦点1(优惠券错误提示模糊)",
        "coupon-input" in product and "操作失败，请重试" in product,
    )

    checkout = page_contents.get("/site/checkout.html", "")
    # 用 ship-express 输入的 checked 属性串精确定位，避免匹配 JS 里的 .checked 字样。
    record(
        report,
        "结算页埋入摩擦点2(默认勾选加急配送,运费计入总价)",
        'data-testid="ship-express" checked' in checkout and "¥924" in checkout,
    )
    record(
        report,
        "结算页埋入摩擦点3(表单校验失败错误提示模糊)",
        "出错了，请检查后重试" in checkout and "error-box" in checkout,
    )
    record(
        report,
        "结算页埋入摩擦点4(验证码提示埋在底部,需滚动可见)",
        "verify-code" in checkout and "verify-hint" in checkout and "8204" in checkout,
    )

    success = page_contents.get("/site/success.html", "")
    record(
        report,
        "成功页含订单号与支付金额(成功判定依据)",
        "支付成功" in success and "order-id" in success and "paid-amount" in success,
    )

    tasks = get_mvp_tasks()
    site_urls = [t.start_url for t in tasks]
    record(
        report,
        "MVP 样例 task start_url 全部指向测试站点",
        all("/site/" in u for u in site_urls),
        f"urls={site_urls}",
    )


# ============================ batch run 与对比报告验收（S-009） ============================ #


def check_batch_compare(report: AcceptanceReport) -> None:
    """验收路径:batch run 与跨 persona 对比报告(S-009)。

    不依赖 LLM:batch run 注入受控 workflow,对比报告聚合用纯代码验证。
    """

    print("\n[路径 6] batch run 与跨 persona 对比报告")
    entity_store = get_entity_store()
    personas = []
    for i in range(3):
        persona = Persona(name=f"批量用户{i}", skill_level="intermediate")
        entity_store.create_persona(persona)
        personas.append(persona)
    task = Task(name="批量对比任务", start_url="http://testserver", max_steps=5)
    entity_store.create_task(task)

    # === batch API:受控 workflow,3 个 persona → 3 个 run ===
    with patch("backend.api.routes.runs.run_formal_workflow", new=_scripted_formal_workflow):
        batch_resp = client.post("/api/v1/runs/batch", json={
            "task_id": task.id,
            "persona_ids": [p.id for p in personas],
            "run_name": "acceptance-batch",
        })
    record(report, "POST /runs/batch 返回 200", batch_resp.status_code == 200, batch_resp.text)
    batch_data = batch_resp.json().get("data", {})
    run_ids = batch_data.get("run_ids", [])
    record(report, "batch 返回 3 个 run_id", len(run_ids) == 3, f"len={len(run_ids)}")
    record(report, "batch 返回 task_id 一致", batch_data.get("task_id") == task.id)

    _drain_formal_background_tasks()

    all_succeeded = all(
        client.get(f"/api/v1/runs/{rid}").json().get("data", {}).get("status") == "succeeded"
        for rid in run_ids
    )
    record(report, "batch 启动的 3 个 run 全部 succeeded", all_succeeded)

    # === compare API:对这 3 个 run 聚合 ===
    compare_resp = client.post("/api/v1/runs/compare", json={"run_ids": run_ids})
    record(report, "POST /runs/compare 返回 200", compare_resp.status_code == 200, compare_resp.text)
    compare_data = compare_resp.json().get("data", {})
    record(report, "对比报告 run_count=3", compare_data.get("run_count") == 3, f"run_count={compare_data.get('run_count')}")
    record(report, "对比报告 success_count=3", compare_data.get("success_count") == 3)
    record(report, "对比报告 conclusion_distribution 全 keep",
           compare_data.get("conclusion_distribution") == {"keep": 3, "optimize": 0, "fix": 0},
           f"dist={compare_data.get('conclusion_distribution')}")
    record(report, "对比报告 items 数量=3", len(compare_data.get("items", [])) == 3)
    record(report, "对比报告含 comparison_summary", bool(compare_data.get("comparison_summary")))

    # === 聚合多样性:直接 store 写入不同结论的 run,验证纯函数聚合 ===
    store = get_run_store()

    def _make_compare_run(persona, *, success, conclusion, total_steps, friction_signals=None) -> str:
        run_id = f"acceptance-compare-{persona.id}"
        rec = RunRecord(run_id=run_id, request=RunRequest(run_name="compare"), persona=persona, task=task)
        store.create_run(rec)
        rep = RunReport(
            run_id=run_id,
            status="succeeded" if success else "failed",
            summary=f"{conclusion} 演示 run",
            success=success,
            conclusion=conclusion,
            persona=persona,
            task=task,
            total_steps=total_steps,
            friction_signals=friction_signals or [],
        )
        store.complete_run(run_id, rep)
        return run_id

    r_keep = _make_compare_run(personas[0], success=True, conclusion="keep", total_steps=3)
    r_opt = _make_compare_run(personas[1], success=True, conclusion="optimize", total_steps=5, friction_signals=["stuck_page"])
    r_fix = _make_compare_run(personas[2], success=False, conclusion="fix", total_steps=7)

    try:
        cmp = build_compare_report([r_keep, r_opt, r_fix], store)
        record(report, "纯函数聚合 run_count=3", cmp.run_count == 3)
        record(report, "纯函数聚合 success_count=2", cmp.success_count == 2)
        record(report, "纯函数聚合 conclusion_distribution={keep:1,optimize:1,fix:1}",
               cmp.conclusion_distribution == {"keep": 1, "optimize": 1, "fix": 1},
               f"dist={cmp.conclusion_distribution}")
        record(report, "纯函数聚合 avg_steps=5.0", cmp.avg_steps == 5.0, f"avg={cmp.avg_steps}")
        record(report, "纯函数聚合 total_friction_signals=1", cmp.total_friction_signals == 1)
    except Exception as exc:  # noqa: BLE001 - 验收脚本局部捕获，避免中断后续 404 检查
        record(report, "纯函数聚合未抛错", False, f"{type(exc).__name__}: {exc}")

    # === 错误分支:compare 不存在 run → 404 ===
    not_found_resp = client.post("/api/v1/runs/compare", json={"run_ids": [r_keep, "ghost"]})
    record(report, "compare 不存在 run 返回 404", not_found_resp.status_code == 404, f"code={not_found_resp.status_code}")


# ============================ S-010 摩擦实验验收 ============================ #


def _sample_persona_by_name(name: str) -> Persona:
    for persona in get_mvp_personas():
        if persona.name == name:
            return Persona(**persona.model_dump())
    raise ValueError(f"Persona sample not found: {name}")


def _sample_task_by_name(name: str) -> Task:
    for task in get_mvp_tasks():
        if task.name == name:
            return Task(**task.model_dump())
    raise ValueError(f"Task sample not found: {name}")


def _store_friction_experiment_run(experiment: FrictionExperiment, task: Task | None = None) -> str:
    store = get_run_store()
    record = RunRecord(
        run_id=f"acceptance-friction-{experiment.experiment_id}",
        request=RunRequest(run_name=experiment.experiment_id),
        persona=_sample_persona_by_name(experiment.persona_name),
        task=task or _sample_task_by_name(experiment.task_name),
    )
    store.create_run(record)
    steps = experiment.build_steps()
    for step in steps:
        store.add_step(record.run_id, step)
    report = build_run_report_without_llm(record, steps)
    store.complete_run(record.run_id, report)
    return record.run_id


def check_friction_experiments(report: AcceptanceReport) -> None:
    """验收路径:多 persona 摩擦实验集(S-010)。"""

    print("\n[路径 7] 多 persona 摩擦实验集")
    experiments = get_friction_experiments()
    record(report, "摩擦实验 fixture 数量=4", len(experiments) == 4, f"len={len(experiments)}")

    task_cache = {task.name: _sample_task_by_name(task.name) for task in get_mvp_tasks()}
    run_ids_by_experiment: dict[str, str] = {}
    for experiment in experiments:
        run_id = _store_friction_experiment_run(experiment, task=task_cache[experiment.task_name])
        run_ids_by_experiment[experiment.experiment_id] = run_id
        stored_report = get_run_store().get_report(run_id)
        expected_signals = set(experiment.expected_friction_signals)
        actual_signals = set(stored_report.friction_signals if stored_report else [])
        record(
            report,
            f"实验 {experiment.experiment_id} 报告已生成",
            stored_report is not None,
        )
        record(
            report,
            f"实验 {experiment.experiment_id} conclusion={experiment.expected_conclusion}",
            stored_report is not None and stored_report.conclusion == experiment.expected_conclusion,
            f"conclusion={stored_report.conclusion if stored_report else None}",
        )
        record(
            report,
            f"实验 {experiment.experiment_id} 命中预期摩擦信号",
            expected_signals.issubset(actual_signals),
            f"expected={sorted(expected_signals)}, actual={sorted(actual_signals)}",
        )

    checkout_compare = build_compare_report(
        [run_ids_by_experiment["E-001"], run_ids_by_experiment["E-002"]],
        get_run_store(),
    )
    checkout_items = {item.persona.name: item for item in checkout_compare.items}
    record(report, "结算实验对比 run_count=2", checkout_compare.run_count == 2)
    record(report, "结算实验对比 success_count=1", checkout_compare.success_count == 1)
    record(
        report,
        "结算实验中新手摩擦信号数高于专家",
        checkout_items["新手用户"].friction_signal_count > checkout_items["专家用户"].friction_signal_count,
        f"newbie={checkout_items['新手用户'].friction_signal_count}, expert={checkout_items['专家用户'].friction_signal_count}",
    )

    coupon_compare = build_compare_report(
        [run_ids_by_experiment["E-003"], run_ids_by_experiment["E-004"]],
        get_run_store(),
    )
    coupon_items = {item.persona.name: item for item in coupon_compare.items}
    record(report, "优惠券实验对比 run_count=2", coupon_compare.run_count == 2)
    record(report, "优惠券实验对比 success_count=1", coupon_compare.success_count == 1)
    record(
        report,
        "优惠券实验中老年用户成功而新手用户失败",
        coupon_items["老年用户"].success is True and coupon_items["新手用户"].success is False,
    )


# ============================ 验收报告渲染 ============================ #


def _render_acceptance_report(report: AcceptanceReport) -> str:
    """渲染 Markdown 验收报告。"""

    lines: list[str] = []
    lines.append("# Synthetic User Lab MVP 验收报告\n")
    lines.append(f"- **开始时间**: {report.started_at}")
    lines.append(f"- **结束时间**: {report.finished_at}")
    lines.append(f"- **用例总数**: {report.total}")
    lines.append(f"- **通过**: {report.passed_count}")
    lines.append(f"- **失败**: {report.failed_count}")
    lines.append(f"- **整体结论**: {'PASS' if report.all_passed else 'FAIL'}")
    if report.demo_run_id:
        lines.append(f"- **Demo Run ID**: {report.demo_run_id}")
    if report.formal_run_id:
        lines.append(f"- **Formal Run ID**: {report.formal_run_id}")
    lines.append("")

    lines.append("## 用例明细\n")
    lines.append("| # | 用例 | 结果 |")
    lines.append("|---|------|------|")
    for idx, r in enumerate(report.results, 1):
        flag = "PASS" if r.passed else "FAIL"
        lines.append(f"| {idx} | {r.name} | {flag} |")
    lines.append("")

    if report.demo_markdown:
        lines.append("## Demo Run Markdown 报告（节选）\n")
        lines.append("````markdown")
        snippet = report.demo_markdown[:1500]
        lines.append(snippet + ("\n...（已截断）" if len(report.demo_markdown) > 1500 else ""))
        lines.append("````")
        lines.append("")

    if report.formal_markdown:
        lines.append("## Formal Run Markdown 报告（节选）\n")
        lines.append("````markdown")
        snippet = report.formal_markdown[:1500]
        lines.append(snippet + ("\n...（已截断）" if len(report.formal_markdown) > 1500 else ""))
        lines.append("````")
        lines.append("")

    return "\n".join(lines)


# ============================ 主入口 ============================ #


def run_acceptance() -> AcceptanceReport:
    """执行全部验收用例。"""

    _reset_stores()
    report = AcceptanceReport(started_at=datetime.now(timezone.utc).isoformat())
    print("Synthetic User Lab MVP 验收开始\n" + "=" * 50)

    try:
        check_demo_run_path(report)
        check_formal_run_path(report)
        check_error_branches(report)
        check_knowledge_retrieval(report)
        check_test_site(report)
        check_batch_compare(report)
        check_friction_experiments(report)
    except Exception as exc:  # noqa: BLE001 - 验收脚本需捕获中断并记录
        traceback.print_exc()
        record(report, "验收流程未中断", False, f"{type(exc).__name__}: {exc}")

    report.finished_at = datetime.now(timezone.utc).isoformat()
    _reset_stores()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="MVP 端到端验收脚本")
    parser.add_argument("--keep-reports", action="store_true", help="保留历史验收报告，不清理目录")
    args = parser.parse_args()

    report = run_acceptance()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not args.keep_reports:
        for old in REPORT_DIR.glob("acceptance-*.md"):
            old.unlink()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"acceptance-{stamp}.md"
    report_path.write_text(_render_acceptance_report(report), encoding="utf-8")
    latest_path = REPORT_DIR / "latest.md"
    latest_path.write_text(_render_acceptance_report(report), encoding="utf-8")

    print("\n" + "=" * 50)
    print(f"验收完成：{report.passed_count}/{report.total} 通过，{report.failed_count} 失败")
    print(f"验收报告已写入: {report_path}")
    print(f"最新报告副本: {latest_path}")

    # 退出码：全部通过返回 0，便于 CI 判定
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

# ============================ Demo Run 图编排模块 ============================ #
# 使用技术栈: Python / LangGraph / Playwright
# 模块功能: 组织 demo run 的页面观察、动作决策、执行、验证、日志和报告流程
# 模块数据流: RunRequest -> StateGraph -> StepLog[] / RunReport
# 模块接口说明: run_demo_workflow() 执行一次完整 demo run

from pathlib import Path

from langgraph.graph import END, START, StateGraph

from backend.analysis.report_builder import build_run_report
from backend.analysis.validator import validate_progress
from backend.core.config import get_settings
from backend.execution.observer import observe_page
from backend.execution.playwright_adapter import close_browser_session, create_browser_session, execute_action
from backend.graph.run_state import DemoRunState
from backend.schemas.run_schemas import ActionInput, DemoPersona, DemoTask, RunRecord, RunRequest, StepLog
from backend.stores.in_memory_run_store import run_store


async def load_demo_context(state: DemoRunState) -> dict:
    """加载固定 demo persona 与 task。"""

    settings = get_settings()
    start_url = f"{state['app_base_url']}/demo/index.html"
    persona = DemoPersona()
    task = DemoTask(start_url=start_url, max_steps=settings.run_step_limit)

    record = state.get("record")
    if record is None:
        record = RunRecord(run_id=state["run_id"], request=state["request"], persona=persona, task=task)
        run_store.create_run(record)
    else:
        record.persona = persona
        record.task = task

    run_store.mark_running(record.run_id)
    return {
        "persona": persona,
        "task": task,
        "record": record,
        "step_logs": [],
        "current_step_index": 0,
        "should_stop": False,
    }


async def init_session(state: DemoRunState) -> dict:
    """创建浏览器会话并进入起始页面。"""

    request = state["request"]
    settings = get_settings()
    headless = settings.browser_headless if request.headless is None else request.headless
    session = await create_browser_session(headless=headless)
    page = session["page"]
    task = state.get("task")
    if task is None:
        raise ValueError("Task is missing before session initialization.")
    await page.goto(task.start_url, wait_until="domcontentloaded")
    return {"session": session}


async def observe_current_page(state: DemoRunState) -> dict:
    """观察当前页面。"""

    session = state.get("session")
    if session is None:
        raise ValueError("Session is missing before page observation.")
    page = session["page"]
    page_state = await observe_page(page)
    return {"current_page_state": page_state}


def decide_next_action(state: DemoRunState) -> dict:
    """根据当前页面状态选择下一步受控动作。"""

    page_state = state.get("current_page_state")
    if page_state is None:
        raise ValueError("Page state is missing before action decision.")
    request = state["request"]

    clickable_selectors = {element.selector for element in page_state.clickable_elements}
    form_field_values = {field.selector: field.value for field in page_state.form_fields}

    action: ActionInput
    if "#start-demo" in clickable_selectors:
        action = ActionInput(action="click", target="#start-demo", reason="进入 demo 表单页面。")
    elif form_field_values.get("#user-name", "") == "":
        action = ActionInput(action="fill", target="#user-name", value=request.expected_user_name, reason="先填写用户名。")
    elif form_field_values.get("#user-email", "") == "":
        action = ActionInput(action="fill", target="#user-email", value=request.expected_email, reason="继续填写邮箱。")
    elif "#submit-demo" in clickable_selectors:
        action = ActionInput(action="click", target="#submit-demo", reason="表单已完整，执行提交。")
    else:
        action = ActionInput(action="wait", target="page", value="300", reason="等待页面状态稳定。")

    return {"current_action": action}


async def execute_current_action(state: DemoRunState) -> dict:
    """执行当前动作并截图。"""

    session = state.get("session")
    action = state.get("current_action")
    current_step_index = state.get("current_step_index", 0)
    if session is None or action is None:
        raise ValueError("Session or action is missing before action execution.")

    page = session["page"]
    step_index = current_step_index + 1
    screenshot_path = Path(state["screenshot_dir"]) / state["run_id"] / f"step-{step_index}.png"
    result = await execute_action(page, action, screenshot_path=screenshot_path)
    return {"current_execution_result": result}


async def validate_current_progress(state: DemoRunState) -> dict:
    """再次观察页面并验证当前执行结果。"""

    session = state.get("session")
    task = state.get("task")
    execution_result = state.get("current_execution_result")
    if session is None or task is None or execution_result is None:
        raise ValueError("Validation prerequisites are missing.")

    page = session["page"]
    page_state = await observe_page(page)
    validation = validate_progress(
        task=task,
        observed_page_state=page_state,
        execution_result=execution_result,
        previous_steps=state.get("step_logs", []),
        current_step_index=state.get("current_step_index", 0) + 1,
    )
    return {
        "current_page_state": page_state,
        "current_validation_result": validation,
        "should_stop": validation.should_stop,
    }


def log_current_step(state: DemoRunState) -> dict:
    """写入当前步骤日志。"""

    page_state = state.get("current_page_state")
    action = state.get("current_action")
    execution_result = state.get("current_execution_result")
    validation_result = state.get("current_validation_result")
    current_step_index = state.get("current_step_index", 0)
    step_logs = state.get("step_logs", [])
    if page_state is None or action is None or execution_result is None or validation_result is None:
        raise ValueError("Step log prerequisites are missing.")

    step_index = current_step_index + 1
    step_log = StepLog(
        step_index=step_index,
        observed_page_state=page_state,
        decided_action=action,
        execution_result=execution_result,
        validation_result=validation_result,
    )
    updated_steps = [*step_logs, step_log]
    run_store.add_step(state["run_id"], step_log)
    return {"step_logs": updated_steps, "current_step_index": step_index}


def route_after_log(state: DemoRunState) -> str:
    """根据当前结果决定继续还是结束。"""

    return "finalize_report" if state.get("should_stop", False) else "observe_page"


async def finalize_report(state: DemoRunState) -> dict:
    """生成最终报告并清理浏览器会话。"""

    record = state.get("record")
    if record is None:
        raise ValueError("Run record is missing before report generation.")

    try:
        report = build_run_report(record, state.get("step_logs", []))
        run_store.complete_run(state["run_id"], report)
        return {"report": report}
    finally:
        await close_browser_session(state.get("session"))


def build_demo_run_graph():
    """构建最小 demo run LangGraph。"""

    workflow = StateGraph(DemoRunState)
    workflow.add_node("load_demo_context", load_demo_context)
    workflow.add_node("init_session", init_session)
    workflow.add_node("observe_page", observe_current_page)
    workflow.add_node("decide_action", decide_next_action)
    workflow.add_node("execute_action", execute_current_action)
    workflow.add_node("validate_progress", validate_current_progress)
    workflow.add_node("log_step", log_current_step)
    workflow.add_node("finalize_report", finalize_report)

    workflow.add_edge(START, "load_demo_context")
    workflow.add_edge("load_demo_context", "init_session")
    workflow.add_edge("init_session", "observe_page")
    workflow.add_edge("observe_page", "decide_action")
    workflow.add_edge("decide_action", "execute_action")
    workflow.add_edge("execute_action", "validate_progress")
    workflow.add_edge("validate_progress", "log_step")
    workflow.add_conditional_edges(
        "log_step",
        route_after_log,
        {"finalize_report": "finalize_report", "observe_page": "observe_page"},
    )
    workflow.add_edge("finalize_report", END)
    return workflow.compile()


async def run_demo_workflow(run_id: str, request: RunRequest, app_base_url: str, screenshot_dir: Path):
    """执行一次完整 demo run。"""

    graph = build_demo_run_graph()
    initial_state: DemoRunState = {
        "run_id": run_id,
        "request": request,
        "app_base_url": app_base_url,
        "screenshot_dir": screenshot_dir,
    }

    try:
        return await graph.ainvoke(initial_state)
    except Exception as exc:
        run_store.fail_run(run_id, str(exc))
        raise exc

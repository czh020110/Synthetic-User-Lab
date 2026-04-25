from __future__ import annotations

# ============================ Demo Run 图编排模块 ============================ #
# 使用技术栈: Python / LangGraph / Playwright
# 模块功能: 组织 demo run 的页面观察、动作决策、执行、验证、日志和报告流程
# 模块数据流: RunRequest -> StateGraph -> StepLog[] / RunReport
# 模块接口说明: run_demo_workflow() 执行一次完整 demo run

import logging
from pathlib import Path
from typing import Any, cast
from pydantic import SecretStr
from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()

from backend.analysis.report_builder import build_run_report  # 生成最终的运行报告
from backend.core.config import get_settings  # 读取全局配置
settings = get_settings()

from backend.execution.observer import observe_page  # 观察到的页面结果
from backend.execution.playwright_adapter import close_browser_session, create_browser_session, execute_action  # playwright 执行动作(浏览器)
from backend.graph.run_state import DemoRunState  # LangGraph 使用的状态类型
from backend.schemas.run_schemas import ActionInput, DemoPersona, DemoTask, RunRecord, RunRequest, StepLog, ValidationResult  # 关键结构schema
from backend.stores.in_memory_run_store import run_store  # 存放在内存的记录和摘要(内存运行存储实例)

from backend.graph.graph_prompt import decide, decide_input, validate, validate_input

logger = logging.getLogger(__name__)


def build_history_summary(step_logs: list[StepLog]) -> str:
    if not step_logs:
        return "暂无历史步骤。"
    return "\n".join(
        f"第{step.step_index}步: 动作={step.decided_action.action} 目标={step.decided_action.target} "
        f"执行成功={step.execution_result.success} 验证状态={step.validation_result.status} "
        f"总结={step.validation_result.progress_summary}"
        for step in step_logs
    )


# ===== 创建agent ===== #
decide_system_prompt = ChatPromptTemplate.from_template(decide)
decide_input_prompt = ChatPromptTemplate.from_messages(
    [
        ("user",decide_input)
    ]
)
validate_system_prompt = ChatPromptTemplate.from_template(validate)
validate_input_prompt = ChatPromptTemplate.from_messages(
    [
        ("user", validate_input)
    ]
)

if settings.model_provider == "openai":
    from langchain_openai import ChatOpenAI
    model = ChatOpenAI(
        model=settings.model_name,
        api_key=SecretStr(settings.api_key) if settings.api_key else None,
        base_url=settings.base_url or None,
    )
elif settings.model_provider == "dashscope":
    from langchain_community.chat_models.tongyi import ChatTongyi
    model = ChatTongyi(
        model=settings.model_name,
        api_key=SecretStr(settings.api_key) if settings.api_key else None,
    )

# =============== #

# graph中的第一个业务节点, 初始化上下文
async def load_demo_context(state: DemoRunState) -> dict:
    """加载固定 demo persona 与 task。"""
    # 使用固定demo配置跑通闭环, 加载demo的人格

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

    decide_agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer,
        system_prompt=decide_system_prompt.format(
            persona=persona.model_dump_json(indent=2),
            task=task.model_dump_json(indent=2),
        ),
        response_format=ActionInput
    )
    validate_agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer,
        system_prompt=validate_system_prompt.format(
            persona=persona.model_dump_json(indent=2),
            task=task.model_dump_json(indent=2),
        ),
        response_format=ValidationResult
    )

    run_store.mark_running(record.run_id)
    return {
        "persona": persona,
        "task": task,
        "record": record,
        "decide_agent": decide_agent,
        "validate_agent": validate_agent,
        "step_logs": [],
        "current_step_index": 0,
        "should_stop": False,
    }


async def init_session(state: DemoRunState) -> dict:
    """创建浏览器会话并进入起始页面。"""

    request = state["request"]
    headless = settings.browser_headless if request.headless is None else request.headless
    logger.info("initializing run session, run_id=%s headless=%s", state["run_id"], headless)
    session = await create_browser_session(headless=headless)  # playwright会话
    page = session["page"]
    task = state.get("task")
    if task is None:
        raise ValueError("Task is missing before session initialization.")
    await page.goto(task.start_url, wait_until="domcontentloaded")
    logger.info("session initialized, run_id=%s start_url=%s", state["run_id"], task.start_url)
    return {"session": session}


async def observe_current_page(state: DemoRunState) -> dict:
    """观察当前页面。"""

    session = state.get("session")
    if session is None:
        raise ValueError("Session is missing before page observation.")
    page = session["page"]
    page_state = await observe_page(page)
    return {"current_page_state": page_state}
    # 返回ObservedPageState对象,存放在current_page_state里面,即页面观察信息

async def decide_next_action(state: DemoRunState) -> dict:
    """根据当前页面状态选择下一步受控动作。"""

    page_state = state.get("current_page_state")
    if page_state is None:
        raise ValueError("Page state is missing before action decision.")
    # ObservedPageState对象里的可点击元素和表单元素
    clickable_selectors = {element.selector for element in page_state.clickable_elements}
    form_field_values = {field.selector: field.value for field in page_state.form_fields}

    persona = state.get("persona")
    task = state.get("task")
    if persona is None or task is None:
        raise ValueError("Persona or task is missing before action decision.")

    step_logs = state.get("step_logs", [])
    agent_messages = decide_input_prompt.format_messages(
        current_page_state=page_state.model_dump_json(indent=2),
        clickable_selectors=sorted(clickable_selectors),
        form_field_values=form_field_values,
        history_summary=build_history_summary(step_logs),
        recent_steps=[step.model_dump(mode="json") for step in step_logs[-3:]],
        previous_steps_count=len(step_logs),
    )
    decide_agent = state.get("decide_agent")
    if decide_agent is None:
        raise ValueError("Decide agent is missing before action decision.")
    agent_config: Any = {"configurable": {"thread_id": f"{state['run_id']}:decide"}}
    response = await decide_agent.ainvoke(cast(Any, {"messages": agent_messages}), config=agent_config)
    action = ActionInput.model_validate(response["structured_response"])

    return {"current_action": action}


async def execute_current_action(state: DemoRunState) -> dict:
    """执行当前动作并截图。"""
    # 执行上一步的动作并截图

    session = state.get("session")
    action = state.get("current_action")
    current_step_index = state.get("current_step_index", 0)
    if session is None or action is None:
        raise ValueError("Session or action is missing before action execution.")

    page = session["page"]
    step_index = current_step_index + 1
    screenshot_path = Path(state["screenshot_dir"]) / state["run_id"] / f"step-{step_index}.png"
    result = await execute_action(page, action, screenshot_path=screenshot_path)  # 真正的执行动作的函数
    return {"current_execution_result": result}


async def validate_current_progress(state: DemoRunState) -> dict:
    """再次观察页面并验证当前执行结果。"""
    # 动作执行完毕后再次观察界面并验证动作执行结果

    session = state.get("session")
    task = state.get("task")
    execution_result = state.get("current_execution_result")
    if session is None or task is None or execution_result is None:
        raise ValueError("Validation prerequisites are missing.")

    page = session["page"]
    page_state = await observe_page(page)
    current_step_index = state.get("current_step_index", 0) + 1
    persona = state.get("persona")
    if persona is None:
        raise ValueError("Persona is missing before progress validation.")
    step_logs = state.get("step_logs", [])
    agent_messages = validate_input_prompt.format_messages(
        latest_page_state=page_state.model_dump_json(indent=2),
        execution_result=execution_result.model_dump_json(indent=2),
        history_summary=build_history_summary(step_logs),
        recent_steps=[step.model_dump(mode="json") for step in step_logs[-3:]],
        current_step_index=current_step_index,
        max_steps=task.max_steps,
    )
    validate_agent = state.get("validate_agent")
    if validate_agent is None:
        raise ValueError("Validate agent is missing before progress validation.")
    agent_config: Any = {"configurable": {"thread_id": f"{state['run_id']}:validate"}}
    response = await validate_agent.ainvoke(cast(Any, {"messages": agent_messages}), config=agent_config)
    validation = ValidationResult.model_validate(response["structured_response"])  # agent 格式化输出的字段存放在"structured_response"中
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
    # 套件边的路由函数(condition edge)
    """根据当前结果决定继续还是结束。"""
    # 判断是否继续, 停止则直接返回报告

    return "finalize_report" if state.get("should_stop", False) else "observe_page"


async def finalize_report(state: DemoRunState) -> dict:
    """生成最终报告并清理浏览器会话。"""

    record = state.get("record")
    if record is None:
        raise ValueError("Run record is missing before report generation.")

    try:
        report = build_run_report(record, state.get("step_logs", []))
        run_store.complete_run(state["run_id"], report)  # 写回并标记状态
        return {"report": report}  # 将report写回
    finally:
        await close_browser_session(state.get("session"))  # 关闭当前会话(浏览器)


def build_demo_run_graph():
    """构建最小 demo run LangGraph。"""

    workflow = StateGraph(DemoRunState)
    workflow.add_node("load_demo_context", load_demo_context)
    workflow.add_node("init_session", init_session)
    workflow.add_node("observe_page", observe_current_page)
    workflow.add_node("decide_action", decide_next_action)  # agent
    workflow.add_node("execute_action", execute_current_action)
    workflow.add_node("validate_progress", validate_current_progress)  # agent
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
        "log_step",  # 起始node
        route_after_log,  # 路由函数
        {"finalize_report": "finalize_report", "observe_page": "observe_page"},  # 满足条件的下一个node
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
        error_message = f"{type(exc).__name__}: {repr(exc)}"
        logger.exception("demo workflow failed, run_id=%s", run_id)
        run_store.fail_run(run_id, error_message)

        record = run_store.get_record(run_id)
        if record is not None and run_store.get_report(run_id) is None:
            report = build_run_report(record, run_store.get_steps(run_id) or [])
            report = report.model_copy(
                update={
                    "status": "failed",
                    "success": False,
                    "summary": f"运行异常中断: {error_message}",
                    "key_findings": [
                        *report.key_findings,
                        f"异常: {error_message}",
                    ],
                }
            )
            run_store.complete_run(run_id, report)
        raise

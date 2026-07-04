from __future__ import annotations

# ============================ 通用 Run 图编排模块 ============================ #
# 使用技术栈: Python / LangGraph / Playwright
# 模块功能: 组织页面观察、动作决策、执行、验证、日志和报告流程
# 模块数据流: RunRequest -> StateGraph -> StepLog[] / RunReport
# 模块接口说明: run_workflow() 执行一次完整 run

import asyncio
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, SecretStr, ValidationError

from backend.analysis.report_builder import build_run_report_async, build_run_report_without_llm
from backend.analysis.validator import validate_progress
from backend.core.config import get_settings
from backend.execution.observer import observe_page
from backend.execution.playwright_adapter import TERMINAL_ACTIONS, close_browser_session, create_browser_session, execute_action
from backend.graph.run_state import RunState
from backend.graph.wait_observer import WaitObservationDecision, WaitObservationOptions, observe_until_ready
from backend.prompt.graph import (
    decide,
    decide_input,
    format_retry_input,
    validate,
    validate_input,
    wait_observe,
    wait_observe_input,
)
from backend.retrieval.minimal_context import render_retrieval_context
from backend.retrieval.failure_recovery import choose_recovery_action
from backend.schemas.run_schemas import (
    ActionInput,
    NavigateActionPayload,
    ObservedPageState,
    Persona,
    RunErrorType,
    RunRequest,
    StepLog,
    Task,
    ValidationResult,
    render_action_definitions,
)
from backend.stores import get_entity_store, get_run_store

logger = logging.getLogger(__name__)
MODEL_API_RETRY_LIMIT = 5
MODEL_FORMAT_RETRY_LIMIT = 3
run_store = get_run_store()


class ModelInvocationError(RuntimeError):
    def __init__(self, stage: str, raw_message: str) -> None:
        self.stage = stage
        self.raw_message = raw_message
        super().__init__(raw_message)


def _raw_exception_message(exc: Exception) -> str:
    return str(exc) or repr(exc)


def _format_validation_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {_raw_exception_message(exc)}"


def _format_retry_prompt(response_model: type[BaseModel], error: str) -> HumanMessage:
    schema = json.dumps(response_model.model_json_schema(), ensure_ascii=False, indent=2)
    return HumanMessage(content=format_retry_input.format(schema=schema, error=error))


async def _invoke_agent_with_retries(
    agent: Any,
    messages: list[Any],
    config: Any,
    response_model: type[BaseModel],
    stage: str,
) -> BaseModel:
    """调用 structured agent 并重试 API 失败和格式错误。

    agent 必须是 model.with_structured_output(schema, method='json_mode', include_raw=True)，
    ainvoke 返回 {"raw": AIMessage, "parsed": Model|None, "parsing_error": Exception|None}。
    """
    current_messages = list(messages)
    api_failures = 0
    format_failures = 0
    last_format_error = ""

    while True:
        try:
            result = await agent.ainvoke(current_messages, config=config)
        except Exception as exc:
            api_failures += 1
            if api_failures > MODEL_API_RETRY_LIMIT:
                raise ModelInvocationError(stage, _raw_exception_message(exc)) from exc
            await asyncio.sleep(min(2 ** (api_failures - 1), 30))
            continue

        # include_raw=True 返回 dict；parsed 可能为 None（格式错误时）
        parsed = result.get("parsed") if isinstance(result, dict) else None
        parsing_error = result.get("parsing_error") if isinstance(result, dict) else None

        if parsed is not None and parsing_error is None:
            try:
                return response_model.model_validate(parsed)
            except (KeyError, TypeError, ValidationError):
                # parsed 已是正确类型但 model_validate 因类型不匹配失败，直接返回
                return cast(BaseModel, parsed)

        # 格式错误：parsing_error 存在或 parsed 为 None
        if parsing_error is not None:
            last_format_error = _format_validation_error(parsing_error)
        else:
            last_format_error = "模型返回内容无法解析为预期格式"

        format_failures += 1
        if format_failures > MODEL_FORMAT_RETRY_LIMIT:
            raise ModelInvocationError(stage, f"模型回复格式不正确: {last_format_error}") from parsing_error
        current_messages = [*current_messages, _format_retry_prompt(response_model, last_format_error)]


def build_history_summary(step_logs: list[StepLog]) -> str:
    if not step_logs:
        return "暂无历史步骤。"
    return "\n".join(
        f"第{step.step_index}步: 动作={step.decided_action.action} 参数={step.decided_action.payload.model_dump(mode='json')} "
        f"执行成功={step.execution_result.success} 验证状态={step.validation_result.status} "
        f"总结={step.validation_result.progress_summary}"
        for step in step_logs
    )


# ===== 创建agent ===== #
decide_system_prompt = ChatPromptTemplate.from_template(decide)
decide_input_prompt = ChatPromptTemplate.from_messages([("user", decide_input)])
validate_system_prompt = ChatPromptTemplate.from_template(validate)
validate_input_prompt = ChatPromptTemplate.from_messages([("user", validate_input)])
wait_observe_system_prompt = ChatPromptTemplate.from_template(wait_observe)
wait_observe_input_prompt = ChatPromptTemplate.from_messages([("user", wait_observe_input)])

def _create_chat_model(model_name: str) -> Any:
    settings = get_settings()
    if not settings.api_key:
        raise ValueError("API key is required for the configured model provider.")
    if not model_name:
        raise ValueError("Model name is required for the configured model provider.")

    if settings.model_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=SecretStr(settings.api_key),
            base_url=settings.base_url,
        )
    if settings.model_provider == "dashscope":
        from langchain_community.chat_models.tongyi import ChatTongyi

        return ChatTongyi(
            model=model_name,
            api_key=SecretStr(settings.api_key),
        )
    raise ValueError(f"Unsupported model provider: {settings.model_provider}")


def create_run_agents(persona: Persona, task: Task) -> tuple[Any, Any, Any]:
    """为当前 run 创建决策、验证与等待观察 agent。

    返回的 agent 使用 with_structured_output(method='json_mode', include_raw=True)，
    ainvoke 返回 {"raw": AIMessage, "parsed": Model|None, "parsing_error": Exception|None}。
    """
    settings = get_settings()
    model = _create_chat_model(settings.model_name)
    wait_model = _create_chat_model(settings.fast_model_name or settings.model_name)
    decide_structured = model.with_structured_output(ActionInput, method="json_mode", include_raw=True)
    validate_structured = model.with_structured_output(ValidationResult, method="json_mode", include_raw=True)
    wait_structured = wait_model.with_structured_output(WaitObservationDecision, method="json_mode", include_raw=True)
    return decide_structured, validate_structured, wait_structured


async def init_session(state: RunState) -> dict:
    """创建浏览器会话并进入起始页面。"""

    settings = get_settings()
    request = state["request"]
    headless = settings.browser_headless if request.headless is None else request.headless
    logger.info("initializing run session, run_id=%s headless=%s", state["run_id"], headless)
    session = await create_browser_session(headless=headless)
    session_box = state.get("session_box")
    if session_box is not None:
        session_box["session"] = session
    page = session["page"]
    task = state.get("task")
    if task is None:
        raise ValueError("Task is missing before session initialization.")
    await page.goto(task.start_url, wait_until="domcontentloaded")
    logger.info("session initialized, run_id=%s start_url=%s", state["run_id"], task.start_url)
    return {"session": session}


async def observe_current_page(state: RunState) -> dict:
    """记录动作前或下一轮开始前的页面观察。"""

    session = state.get("session")
    if session is None:
        raise ValueError("Session is missing before page observation.")
    page = session["page"]
    page_state = await observe_page(page)
    return {"current_page_state": page_state}


async def observe_after_action(state: RunState) -> dict:
    """记录动作后的页面快照。"""

    session = state.get("session")
    if session is None:
        raise ValueError("Session is missing before post-action observation.")

    page = session["page"]
    step_index = state.get("current_step_index", 0) + 1
    after_screenshot_path = Path(state["screenshot_dir"]) / state["run_id"] / f"step-{step_index}-after.png"
    page_state = await observe_page(page)
    page_state = page_state.model_copy(update={"screenshot_path": str(after_screenshot_path)})
    after_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(after_screenshot_path), full_page=True)
    return {
        "current_page_state": page_state,
        "post_action_page_state": page_state,
    }


async def decide_next_action(state: RunState) -> dict:
    """根据当前页面状态选择下一步受控动作。"""

    page_state = state.get("current_page_state")
    if page_state is None:
        raise ValueError("Page state is missing before action decision.")

    clickable_selectors = {element.selector for element in page_state.clickable_elements}
    form_field_values = {field.selector: field.value for field in page_state.form_fields}

    persona = state.get("persona")
    task = state.get("task")
    if persona is None or task is None:
        raise ValueError("Persona or task is missing before action decision.")

    step_logs = state.get("step_logs", [])
    retrieval_context_text = render_retrieval_context(state.get("retrieval_context") or [])
    system_message = decide_system_prompt.format(
        persona=persona.model_dump_json(indent=2),
        task=task.model_dump_json(indent=2),
        action_definitions=render_action_definitions(),
    )
    user_messages = decide_input_prompt.format_messages(
        current_page_state=page_state.model_dump_json(indent=2),
        clickable_selectors=sorted(clickable_selectors),
        form_field_values=form_field_values,
        history_summary=build_history_summary(step_logs),
        retrieval_context=retrieval_context_text,
        recent_steps=[step.model_dump(mode="json") for step in step_logs[-3:]],
        previous_steps_count=len(step_logs),
    )
    decide_agent = state.get("decide_agent")
    if decide_agent is None:
        raise ValueError("Decide agent is missing before action decision.")
    all_messages = [SystemMessage(content=system_message), *user_messages]
    action = cast(
        ActionInput,
        await _invoke_agent_with_retries(
            decide_agent,
            all_messages,
            None,
            ActionInput,
            "decide",
        ),
    )

    return {"current_action": action}


async def execute_current_action(state: RunState) -> dict:
    """执行当前动作并记录动作前页面快照。"""

    session = state.get("session")
    action = state.get("current_action")
    task = state.get("task")
    before_page_state = state.get("current_page_state")
    current_step_index = state.get("current_step_index", 0)
    if session is None or action is None or task is None or before_page_state is None:
        raise ValueError("Session, action, task, or page state is missing before action execution.")

    page = session["page"]
    step_index = current_step_index + 1
    before_screenshot_path = Path(state["screenshot_dir"]) / state["run_id"] / f"step-{step_index}-before.png"
    step_before_page_state = before_page_state.model_copy(update={"screenshot_path": str(before_screenshot_path)})
    before_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(before_screenshot_path), full_page=True)

    result = await execute_action(page, action, task)
    return {
        "current_execution_result": result,
        "step_before_page_state": step_before_page_state,
        "post_action_page_state": None,
        "wait_observation_status": None,
        "wait_observation_reason": None,
        "wait_observation_observations": None,
        "wait_observation_elapsed_ms": None,
        "wait_observation_timeout_ms": None,
        "wait_observation_terminal_decision": None,
        "wait_observation_traces": None,
        "wait_observation_round": None,
    }


async def wait_after_action(state: RunState) -> dict:
    """根据等待观察模型判断是否继续等待。"""

    session = state.get("session")
    task = state.get("task")
    wait_agent = state.get("wait_agent")
    persona = state.get("persona")
    if session is None or task is None or wait_agent is None or persona is None:
        raise ValueError("Wait observation prerequisites are missing.")

    page = session["page"]
    step_index = state.get("current_step_index", 0) + 1
    options = WaitObservationOptions()

    wait_step_index = (state.get("wait_observation_round") or 0) + 1

    async def classify_fn(
        page_state,
        elapsed_ms: int,
        observations: int,
        normal_remaining_ms: int,
        abnormal_remaining_ms: int,
    ):
        user_messages = wait_observe_input_prompt.format_messages(
            current_page_state=page_state.model_dump_json(indent=2),
            elapsed_ms=elapsed_ms,
            observations=observations,
            normal_remaining_ms=normal_remaining_ms,
            abnormal_remaining_ms=abnormal_remaining_ms,
        )
        system_message = wait_observe_system_prompt.format(
            persona=persona.model_dump_json(indent=2),
            task=task.model_dump_json(indent=2),
        )
        all_messages = [SystemMessage(content=system_message), *user_messages]
        return cast(
            WaitObservationDecision,
            await _invoke_agent_with_retries(
                wait_agent,
                all_messages,
                None,
                WaitObservationDecision,
                "wait_observe",
            ),
        )

    async def capture_trace_screenshot_fn(observation_index: int) -> str | None:
        screenshot_path = Path(state["screenshot_dir"]) / state["run_id"] / f"step-{step_index}-wait-{observation_index}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)

    result = await observe_until_ready(
        page,
        classify_fn=classify_fn,
        capture_trace_screenshot_fn=capture_trace_screenshot_fn,
        options=options,
    )

    final_screenshot_path = Path(state["screenshot_dir"]) / state["run_id"] / f"step-{step_index}-after.png"
    final_screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(final_screenshot_path), full_page=True)
    post_action_page_state = result.page_state.model_copy(update={"screenshot_path": str(final_screenshot_path)})

    return {
        "current_page_state": post_action_page_state,
        "post_action_page_state": post_action_page_state,
        "wait_observation_status": result.status,
        "wait_observation_reason": result.reason,
        "wait_observation_observations": result.observations,
        "wait_observation_elapsed_ms": result.elapsed_ms,
        "wait_observation_timeout_ms": result.timeout_ms,
        "wait_observation_terminal_decision": result.terminal_decision,
        "wait_observation_traces": [asdict(trace) for trace in result.traces],
        "wait_observation_round": wait_step_index,
    }


def route_after_execute(state: RunState) -> str:
    """wait 交给等待观察，终止动作直接验证，其余观察页面。"""

    action = state.get("current_action")
    if action is not None and action.action == "wait":
        return "wait_after_action"
    if action is not None and action.action in TERMINAL_ACTIONS:
        return "validate_progress"
    return "observe_after_action"


def route_after_validate(state: RunState) -> str:
    """根据验证结果决定是否进入等待观察。"""

    validation = state.get("current_validation_result")
    if validation is None:
        return "log_step"
    if state.get("should_stop", False) or validation.should_stop:
        return "log_step"
    if state.get("wait_observation_status") is not None:
        return "log_step"

    signals = set(validation.friction_signals)
    if "recovery_candidate" in signals:
        return "wait_after_action"
    return "log_step"


def _build_wait_failure_validation(reason: str, signal: str) -> ValidationResult:
    return ValidationResult(
        status="failed",
        should_stop=True,
        progress_summary=reason,
        friction_signals=[signal],
        detected_error=True,
    )


def _build_wait_success_validation(reason: str) -> ValidationResult:
    return ValidationResult(
        status="succeeded",
        should_stop=True,
        progress_summary=reason,
        detected_success=True,
    )


def _build_wait_recovery_validation(reason: str) -> ValidationResult:
    return ValidationResult(
        status="running",
        should_stop=False,
        progress_summary=reason,
        friction_signals=["wait_observe_abnormal_stuck", "recovery_candidate"],
        detected_error=False,
    )


async def validate_current_progress(state: RunState) -> dict:
    """再次观察页面并验证当前执行结果。"""

    session = state.get("session")
    task = state.get("task")
    execution_result = state.get("current_execution_result")
    if session is None or task is None or execution_result is None:
        raise ValueError("Validation prerequisites are missing.")

    current_action = state.get("current_action")
    if current_action is not None and current_action.action in TERMINAL_ACTIONS:
        return {
            "current_page_state": state.get("current_page_state") or ObservedPageState(current_url="", title="", visible_text_summary=""),
            "current_validation_result": ValidationResult(
                status="failed",
                should_stop=True,
                progress_summary=execution_result.detail,
                detected_error=True,
            ),
            "should_stop": True,
        }

    page = session["page"]
    page_state = state.get("current_page_state")
    if page_state is None:
        page_state = await observe_page(page)

    current_step_index = state.get("current_step_index", 0) + 1
    persona = state.get("persona")
    if persona is None:
        raise ValueError("Persona is missing before progress validation.")
    step_logs = state.get("step_logs", [])
    current_action = state.get("current_action")
    action_json = current_action.model_dump_json(indent=2) if current_action is not None else "null"
    wait_status = state.get("wait_observation_status")
    if wait_status == "normal_timeout":
        validation = _build_wait_failure_validation(
            state.get("wait_observation_reason") or "页面正常等待超过上限，仍未进入下一步或完成状态。",
            "wait_observe_normal_timeout",
        )
    elif wait_status == "abnormal_stuck" and not state.get("recovery_attempted", False):
        validation = _build_wait_recovery_validation(
            state.get("wait_observation_reason") or "页面疑似异常卡住，准备执行受控恢复动作。"
        )
    elif wait_status == "abnormal_stuck":
        validation = _build_wait_failure_validation(
            state.get("wait_observation_reason") or "页面疑似异常卡住，恢复后仍无进展。",
            "wait_observe_abnormal_stuck",
        )
    elif wait_status == "success":
        validation = _build_wait_success_validation(state.get("wait_observation_reason") or "等待观察确认任务已完成。")
    else:
        retrieval_context_text = render_retrieval_context(state.get("retrieval_context") or [])
        user_messages = validate_input_prompt.format_messages(
            latest_page_state=page_state.model_dump_json(indent=2),
            current_action=action_json,
            execution_result=execution_result.model_dump_json(indent=2),
            history_summary=build_history_summary(step_logs),
            retrieval_context=retrieval_context_text,
            recent_steps=[step.model_dump(mode="json") for step in step_logs[-3:]],
            current_step_index=current_step_index,
            max_steps=task.max_steps,
            success_criteria=task.success_criteria,
        )
        validate_agent = state.get("validate_agent")
        if validate_agent is None:
            raise ValueError("Validate agent is missing before progress validation.")
        system_message = validate_system_prompt.format(
            persona=persona.model_dump_json(indent=2),
            task=task.model_dump_json(indent=2),
        )
        all_messages = [SystemMessage(content=system_message), *user_messages]
        validation = cast(
            ValidationResult,
            await _invoke_agent_with_retries(
                validate_agent,
                all_messages,
                None,
                ValidationResult,
                "validate",
            ),
        )

    guarded_validation = validate_progress(
        task,
        page_state,
        execution_result,
        step_logs,
        current_step_index,
        current_action=state.get("current_action"),
        agent_validation=validation,
    )
    return {
        "current_page_state": page_state,
        "current_validation_result": guarded_validation,
        "should_stop": guarded_validation.should_stop,
    }


def log_current_step(state: RunState) -> dict:
    """写入当前步骤日志。"""

    page_state = state.get("step_before_page_state")
    post_action_page_state = state.get("post_action_page_state")
    action = state.get("current_action")
    execution_result = state.get("current_execution_result")
    validation_result = state.get("current_validation_result")
    current_step_index = state.get("current_step_index", 0)
    step_logs = state.get("step_logs", [])
    if page_state is None or post_action_page_state is None or action is None or execution_result is None or validation_result is None:
        raise ValueError("Step log prerequisites are missing.")

    step_index = current_step_index + 1
    wait_observation_status = state.get("wait_observation_status")
    wait_observation_reason = state.get("wait_observation_reason")
    wait_observation_observations = state.get("wait_observation_observations")
    wait_observation_elapsed_ms = state.get("wait_observation_elapsed_ms")
    wait_observation_timeout_ms = state.get("wait_observation_timeout_ms")
    wait_observation_terminal_decision = state.get("wait_observation_terminal_decision")
    wait_observation_traces = state.get("wait_observation_traces") or []
    step_log = StepLog(
        step_index=step_index,
        observed_page_state=page_state,
        decided_action=action,
        execution_result=execution_result,
        validation_result=validation_result,
        post_action_page_state=post_action_page_state,
        wait_observation_status=wait_observation_status,
        wait_observation_reason=wait_observation_reason,
        wait_observation_observations=wait_observation_observations,
        wait_observation_elapsed_ms=wait_observation_elapsed_ms,
        wait_observation_timeout_ms=wait_observation_timeout_ms,
        wait_observation_terminal_decision=wait_observation_terminal_decision,
        wait_observation_traces=wait_observation_traces,
        retrieval_context=state.get("retrieval_context") or [],
    )
    updated_steps = [*step_logs, step_log]
    run_store.add_step(state["run_id"], step_log)
    return {"step_logs": updated_steps, "current_step_index": step_index}

# 路由节点路由函数, 条件边
def route_after_log(state: RunState) -> str:
    """根据当前结果决定继续、恢复还是结束。"""

    if state.get("should_stop", False):
        return "finalize_report"
    validation = state.get("current_validation_result")
    signals = set(validation.friction_signals) if validation is not None else set()
    if state.get("wait_observation_status") == "abnormal_stuck" and "recovery_candidate" in signals:
        return "prepare_recovery_action"  # 对于abnormal_stuck即非正常的等待且有恢复信号的
    return "observe_page"

# 更新graph state 确定恢复动作,交给execute_action节点执行
async def prepare_recovery_action(state: RunState) -> dict:
    """根据摩擦信号与恢复历史，动态选择受控恢复动作。"""

    task = state.get("task")
    page_state = state.get("current_page_state")
    validation = state.get("current_validation_result")
    if task is None or page_state is None:
        raise ValueError("Task or page state is missing before recovery action.")

    retrieval_context = state.get("retrieval_context", [])
    step_logs = state.get("step_logs", [])
    recovery_history = state.get("recovery_history") or []

    friction_signals = list(validation.friction_signals) if validation is not None else []

    recovery_action = choose_recovery_action(
        task=task,
        friction_signals=friction_signals,
        step_logs=step_logs,
        recovery_history=recovery_history,
        entity_store=get_entity_store(),
    )

    new_history_entry = {
        "error_pattern": friction_signals[0] if friction_signals else "unknown",
        "action": recovery_action.action,
        "reason": recovery_action.reason,
    }

    return {
        "current_action": recovery_action,
        "current_page_state": page_state,
        "recovery_attempted": True,
        "recovery_history": [*recovery_history, new_history_entry],
        "wait_observation_status": None,
        "wait_observation_reason": None,
        "wait_observation_observations": None,
        "wait_observation_elapsed_ms": None,
        "wait_observation_timeout_ms": None,
        "wait_observation_terminal_decision": None,
        "wait_observation_traces": None,
    }


async def finalize_report(state: RunState) -> dict:
    """生成最终报告并清理浏览器会话。"""

    record = state.get("record")
    if record is None:
        raise ValueError("Run record is missing before report generation.")

    try:
        report = await build_run_report_async(record, state.get("step_logs", []))
        run_store.complete_run(state["run_id"], report)
        return {"report": report}
    finally:
        await close_browser_session(state.get("session"))
        session_box = state.get("session_box")
        if session_box is not None:
            session_box["closed"] = True


def build_run_graph(load_context_node: Any):
    """构建通用 run graph。"""

    workflow = StateGraph(RunState)
    workflow.add_node("load_context", load_context_node)
    workflow.add_node("init_session", init_session)
    workflow.add_node("observe_page", observe_current_page)
    workflow.add_node("observe_after_action", observe_after_action)
    workflow.add_node("decide_action", decide_next_action)
    workflow.add_node("execute_action", execute_current_action)
    workflow.add_node("wait_after_action", wait_after_action)
    workflow.add_node("validate_progress", validate_current_progress)
    workflow.add_node("log_step", log_current_step)
    workflow.add_node("prepare_recovery_action", prepare_recovery_action)
    workflow.add_node("finalize_report", finalize_report)

    workflow.add_edge(START, "load_context")
    workflow.add_edge("load_context", "init_session")
    workflow.add_edge("init_session", "observe_page")
    workflow.add_edge("observe_page", "decide_action")
    workflow.add_edge("decide_action", "execute_action")
    workflow.add_conditional_edges(
        "execute_action",
        route_after_execute,
        {
            "wait_after_action": "wait_after_action",
            "observe_after_action": "observe_after_action",
            "validate_progress": "validate_progress",
        },
    )
    workflow.add_edge("observe_after_action", "validate_progress")
    workflow.add_conditional_edges(
        "validate_progress",
        route_after_validate,
        {"wait_after_action": "wait_after_action", "log_step": "log_step"},
    )
    workflow.add_edge("wait_after_action", "validate_progress")
    workflow.add_conditional_edges(
        "log_step",
        route_after_log,
        {
            "finalize_report": "finalize_report",
            "prepare_recovery_action": "prepare_recovery_action",
            "observe_page": "observe_page",
        },
    )
    workflow.add_edge("prepare_recovery_action", "execute_action")
    workflow.add_edge("finalize_report", END)
    return workflow.compile()


async def run_workflow(
    run_id: str,
    request: RunRequest,
    app_base_url: str,
    screenshot_dir: Path,
    load_context_node: Any,
    extra_initial_state: dict | None = None,
):
    """执行一次完整 run。

    extra_initial_state: 可选的额外初始状态字段，用于正式 run 传入已解析的 persona/task/record。
    """

    graph = build_run_graph(load_context_node)
    initial_state: RunState = {
        "run_id": run_id,
        "request": request,
        "app_base_url": app_base_url,
        "screenshot_dir": screenshot_dir,
        "session_box": {},
    }
    if extra_initial_state:
        initial_state.update(extra_initial_state)

    try:
        return await graph.ainvoke(initial_state)
    except Exception as exc:
        is_model_error = isinstance(exc, ModelInvocationError)
        error_type: RunErrorType = "model_error" if is_model_error else "system_error"
        error_message = exc.raw_message if is_model_error else f"{type(exc).__name__}: {repr(exc)}"
        report_summary = f"模型调用错误: {error_message}" if is_model_error else f"运行异常中断: {error_message}"
        finding = f"模型调用错误: {error_message}" if is_model_error else f"异常: {error_message}"
        logger.exception("run workflow failed, run_id=%s", run_id)
        run_store.fail_run(run_id, error_message, error_type=error_type)

        record = run_store.get_record(run_id)
        if record is not None and run_store.get_report(run_id) is None:
            report = build_run_report_without_llm(record, run_store.get_steps(run_id) or [])
            report = report.model_copy(
                update={
                    "status": "failed",
                    "success": False,
                    "conclusion": "fix",
                    "summary": report_summary,
                    "error_type": error_type,
                    "error_message": error_message,
                    "key_findings": [
                        *report.key_findings,
                        finding,
                    ],
                }
            )
            run_store.complete_run(run_id, report)
        raise
    finally:
        session_box = initial_state.get("session_box") or {}
        session = session_box.get("session")
        if session is not None and not session_box.get("closed", False):
            await close_browser_session(session)
            session_box["closed"] = True

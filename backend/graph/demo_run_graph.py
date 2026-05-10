from __future__ import annotations

# ============================ Demo Run 图编排模块 ============================ #
# 使用技术栈: Python / LangGraph / Playwright
# 模块功能: 提供 demo 场景上下文，并调用通用 run graph 执行完整流程
# 模块数据流: Demo 上下文 -> run_graph -> StepLog[] / RunReport
# 模块接口说明: run_demo_workflow() 执行一次完整 demo run

import logging
from pathlib import Path

from backend.core.config import get_settings
from backend.graph.run_graph import create_run_agents, build_run_graph, run_workflow
from backend.graph.run_state import RunState
from backend.schemas.run_schemas import Persona, RunRecord, RunRequest, Task
from backend.stores.in_memory_run_store import run_store

logger = logging.getLogger(__name__)
settings = get_settings()


def build_demo_persona() -> Persona:
    """构造 demo 默认 persona。"""

    return Persona(
        id="demo-persona-newbie",
        name="新手体验用户",
        description="会按照页面主路径逐步完成任务，不进行高风险操作。",
        skill_level="newbie",
        patience_level="medium",
        risk_preference="low",
    )


def build_demo_task(app_base_url: str) -> Task:
    """构造 demo 默认任务。"""

    return Task(
        id="demo-task-onboarding",
        name="验证当前实现的 demo 任务",
        description="这个 demo 用于验证当前 run 在真实页面流程中的模型决策情况：请进入 demo 页面，按照页面提示完成表单流程，并在页面明确显示任务完成状态后结束。",
        start_url=f"{app_base_url}/demo/index.html",
        success_criteria=[
            "页面明确显示任务完成状态",
            "成功卡片可见",
            "表单已隐藏",
        ],
        max_steps=settings.run_step_limit,
        allowed_actions=["navigate", "click", "fill", "wait"],
        risk_level="low",
        destructive_action_allowed=False,
    )


def create_demo_placeholder_record(run_id: str, request: RunRequest, app_base_url: str) -> RunRecord:
    """构造 demo 占位运行记录。"""

    persona = build_demo_persona()
    task = build_demo_task(app_base_url)
    return RunRecord(run_id=run_id, request=request, persona=persona, task=task)


async def load_demo_context(state: RunState) -> dict:
    """加载 demo 场景的 persona、task、agent 与运行记录。"""

    app_base_url = state["app_base_url"]
    persona = build_demo_persona()
    task = build_demo_task(app_base_url)

    record = state.get("record")
    if record is None:
        record = RunRecord(run_id=state["run_id"], request=state["request"], persona=persona, task=task)
        run_store.create_run(record)
    else:
        record.persona = persona
        record.task = task

    decide_agent, validate_agent, wait_agent = create_run_agents(persona, task)
    run_store.mark_running(record.run_id)
    return {
        "persona": persona,
        "task": task,
        "record": record,
        "decide_agent": decide_agent,
        "validate_agent": validate_agent,
        "wait_agent": wait_agent,
        "step_logs": [],
        "current_step_index": 0,
        "should_stop": False,
    }


def build_demo_run_graph():
    """构建 demo 场景的 run graph。"""

    return build_run_graph(load_demo_context)


async def run_demo_workflow(run_id: str, request: RunRequest, app_base_url: str, screenshot_dir: Path):
    """执行一次完整 demo run。"""

    return await run_workflow(run_id, request, app_base_url, screenshot_dir, load_demo_context)

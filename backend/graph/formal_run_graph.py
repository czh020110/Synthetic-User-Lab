from __future__ import annotations

# ============================ 正式 Run 图编排模块 ============================ #
# 模块功能: 提供正式 run 的上下文加载与工作流执行
# 模块数据流: API 解析的 persona/task -> run_graph -> StepLog[] / RunReport
# 模块接口说明: run_formal_workflow() 执行一次引用 persona_id/task_id 的正式 run

import logging
from pathlib import Path

from backend.graph.run_graph import build_run_graph, create_run_agents, run_workflow
from backend.graph.run_state import RunState
from backend.retrieval import build_retrieval_context
from backend.schemas.run_schemas import Persona, RunRecord, RunRequest, Task
from backend.stores import get_run_store

logger = logging.getLogger(__name__)


async def load_formal_context(state: RunState) -> dict:
    """加载正式 run 的 persona、task、agent 与运行记录。

    与 load_demo_context 的区别：persona/task 已在 API 层解析并注入 state，
    不需要重新构建。record 也已由 API 层创建并存入 RunStore。
    """

    run_store = get_run_store()
    persona = state.get("persona")
    task = state.get("task")
    if persona is None or task is None:
        raise ValueError("Persona and task must be resolved before formal run context loading.")

    record = state.get("record")
    if record is None:
        raise ValueError("Run record must be created before formal run context loading.")

    retrieval_context = build_retrieval_context(persona, task)
    decide_agent, validate_agent, wait_agent = create_run_agents(persona, task)
    run_store.mark_running(record.run_id)
    return {
        "persona": persona,
        "task": task,
        "record": record,
        "decide_agent": decide_agent,
        "validate_agent": validate_agent,
        "wait_agent": wait_agent,
        "retrieval_context": retrieval_context,
        "step_logs": [],
        "current_step_index": 0,
        "should_stop": False,
    }


async def run_formal_workflow(
    run_id: str,
    request: RunRequest,
    app_base_url: str,
    screenshot_dir: Path,
    persona: Persona,
    task: Task,
    record: RunRecord,
):
    """执行一次正式 run。persona/task 由 API 层解析后传入。"""

    initial_state_extra = {
        "persona": persona,
        "task": task,
        "record": record,
    }
    return await run_workflow(
        run_id=run_id,
        request=request,
        app_base_url=app_base_url,
        screenshot_dir=screenshot_dir,
        load_context_node=load_formal_context,
        extra_initial_state=initial_state_extra,
    )

from __future__ import annotations

# ============================ 报告生成模块 ============================ #
# 使用技术栈: Python / Pydantic / LangChain
# 模块功能: 基于步骤日志整理最终 run 报告，并按本次 run 的证据生成详细报告与建议
# 模块数据流: RunRecord + StepLog[] -> _extract_structured_facts -> (optional) Agent -> RunReport
# 模块接口说明: build_run_report() 返回最终结构化报告, run 结束直接返回报告
# 架构说明: 事实提取层(纯代码) -> Agent语义层(FAST_MODEL) -> 组装层(纯代码)

import json
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from backend.ai_api.model_resolver import resolve_runtime_model
from backend.analysis.friction_analyzer import analyze_friction
from backend.prompt.report import REPORT_ANALYSIS_PROMPT
from backend.schemas.run_schemas import (
    FrictionIssue,
    FrictionSeverity,
    KeyScreenshot,
    ReportConclusion,
    RunRecord,
    RunReport,
    StepLog,
)

RECOMMENDATION_LIMIT = 10
CONCLUSION_SEVERITY_ORDER: dict[ReportConclusion, int] = {
    "keep": 0,
    "optimize": 1,
    "fix": 2,
}


# ============================ 事实提取层 ============================ #


@dataclass
class ReportFacts:
    """代码提取的结构化事实摘要，供 Agent 输入和前端展示。"""

    success: bool
    conclusion: ReportConclusion
    total_steps: int
    error_type: str | None
    error_message: str | None
    friction_signals: list[str]
    friction_issues: list[FrictionIssue]
    first_issue_step: int | None
    first_issue_summary: str | None
    first_issue_error: str | None
    wait_observation_summary: str | None
    persona_impact: str | None
    last_progress_summary: str
    step_action_summary: list[dict[str, Any]]
    key_screenshots: list[KeyScreenshot]


def _extract_structured_facts(record: RunRecord, steps: list[StepLog]) -> ReportFacts:
    """从步骤日志提取结构化事实，不生成模板化文案。"""

    success = bool(steps and steps[-1].validation_result.detected_success)
    last_progress_summary = steps[-1].validation_result.progress_summary if steps else "任务未执行任何步骤。"
    friction_signals = _collect_friction_signals(steps)
    conclusion = _build_conclusion(record, steps, success, friction_signals, last_progress_summary)
    friction_issues = analyze_friction(steps)

    first_issue_step_log = _find_first_issue_step(steps)
    first_issue_summary = None
    first_issue_error = None
    if first_issue_step_log is not None:
        first_issue_summary = first_issue_step_log.validation_result.progress_summary
        if first_issue_step_log.execution_result.error_message:
            first_issue_error = first_issue_step_log.execution_result.error_message

    wait_observation_summary = _build_wait_observation_summary(steps)
    persona_impact = _build_persona_impact(record, friction_signals, success)
    key_screenshots = _extract_key_screenshots(steps, success)

    step_action_summary = [
        {
            "index": step.step_index,
            "action": step.decided_action.action,
            "selector": getattr(step.decided_action.payload, "selector", None),
            "success": step.execution_result.success,
            "validation_summary": step.validation_result.progress_summary,
            "friction_signals": step.validation_result.friction_signals,
            "detected_success": step.validation_result.detected_success,
            "detected_error": step.validation_result.detected_error,
        }
        for step in steps
    ]

    return ReportFacts(
        success=success,
        conclusion=conclusion,
        total_steps=len(steps),
        error_type=record.error_type,
        error_message=record.error_message,
        friction_signals=friction_signals,
        friction_issues=friction_issues,
        first_issue_step=first_issue_step_log.step_index if first_issue_step_log else None,
        first_issue_summary=first_issue_summary,
        first_issue_error=first_issue_error,
        wait_observation_summary=wait_observation_summary,
        persona_impact=persona_impact,
        last_progress_summary=last_progress_summary,
        step_action_summary=step_action_summary,
        key_screenshots=key_screenshots,
    )


# ============================ 公共接口 ============================ #


def build_run_report(record: RunRecord, steps: list[StepLog]) -> RunReport:
    """生成当前 run 的结构化报告。"""

    return _build_run_report_sync(record, steps)


async def build_run_report_async(record: RunRecord, steps: list[StepLog]) -> RunReport:
    """生成当前 run 的结构化报告（异步）。"""

    return await _build_run_report_async(record, steps)


def build_run_report_without_llm(record: RunRecord, steps: list[StepLog]) -> RunReport:
    """生成不依赖模型分析的兜底报告。"""

    return _build_run_report_sync(record, steps, allow_agent=False)


# ============================ 核心构建流程 ============================ #


def _build_run_report_sync(
    record: RunRecord,
    steps: list[StepLog],
    *,
    allow_agent: bool = True,
) -> RunReport:
    facts = _extract_structured_facts(record, steps)

    agent_summary: str | None = None
    agent_conclusion: ReportConclusion | None = None
    agent_key_findings: list[str] = []
    agent_recommendations: list[str] = []

    if allow_agent and _should_call_agent(facts):
        analysis = _generate_report_analysis(facts, record)
        agent_summary = analysis.get("summary")
        agent_conclusion = analysis.get("conclusion")
        agent_key_findings = _dedupe_text_items(analysis.get("key_findings", []))
        agent_recommendations = _dedupe_text_items(analysis.get("next_recommendations", []), limit=RECOMMENDATION_LIMIT)

    final_conclusion = _merge_conclusion(facts.conclusion, agent_conclusion)
    summary = agent_summary or facts.last_progress_summary
    key_findings = agent_key_findings

    return _assemble_report(record, steps, facts, summary, final_conclusion, key_findings, agent_recommendations)


async def _build_run_report_async(record: RunRecord, steps: list[StepLog]) -> RunReport:
    facts = _extract_structured_facts(record, steps)

    agent_summary: str | None = None
    agent_conclusion: ReportConclusion | None = None
    agent_key_findings: list[str] = []
    agent_recommendations: list[str] = []

    if _should_call_agent(facts):
        analysis = await _generate_report_analysis_async(facts, record)
        agent_summary = analysis.get("summary")
        agent_conclusion = analysis.get("conclusion")
        agent_key_findings = _dedupe_text_items(analysis.get("key_findings", []))
        agent_recommendations = _dedupe_text_items(analysis.get("next_recommendations", []), limit=RECOMMENDATION_LIMIT)

    final_conclusion = _merge_conclusion(facts.conclusion, agent_conclusion)
    summary = agent_summary or facts.last_progress_summary
    key_findings = agent_key_findings

    return _assemble_report(record, steps, facts, summary, final_conclusion, key_findings, agent_recommendations)


# ============================ 组装层 ============================ #


def _assemble_report(
    record: RunRecord,
    steps: list[StepLog],
    facts: ReportFacts,
    summary: str,
    conclusion: ReportConclusion,
    key_findings: list[str],
    recommendations: list[str],
) -> RunReport:
    """组装最终 RunReport 模型。"""

    return RunReport(
        run_id=record.run_id,
        status="succeeded" if facts.success else "failed",
        summary=summary,
        success=facts.success,
        conclusion=conclusion,
        persona=record.persona,
        task=record.task,
        total_steps=facts.total_steps,
        friction_signals=facts.friction_signals,
        friction_issues=facts.friction_issues,
        key_findings=key_findings,
        next_recommendations=recommendations,
        step_details=[_serialize_step(step) for step in steps],
        structured_facts=_facts_to_dict(facts),
        key_screenshots=facts.key_screenshots,
        error_type=record.error_type,
        error_message=record.error_message,
    )


def _facts_to_dict(facts: ReportFacts) -> dict[str, Any]:
    """将 ReportFacts 转为可 JSON 序列化的字典。"""

    return {
        "success": facts.success,
        "conclusion": facts.conclusion,
        "total_steps": facts.total_steps,
        "error_type": facts.error_type,
        "error_message": facts.error_message,
        "friction_signals": facts.friction_signals,
        "friction_issues": [issue.model_dump(mode="json") for issue in facts.friction_issues],
        "first_issue_step": facts.first_issue_step,
        "first_issue_summary": facts.first_issue_summary,
        "first_issue_error": facts.first_issue_error,
        "wait_observation_summary": facts.wait_observation_summary,
        "persona_impact": facts.persona_impact,
        "step_action_summary": facts.step_action_summary,
        "key_screenshots": [ks.model_dump(mode="json") for ks in facts.key_screenshots],
    }


# ============================ Agent 语义层 ============================ #


def _should_call_agent(facts: ReportFacts) -> bool:
    """判断是否需要调用 Agent 生成详细报告。"""

    if facts.total_steps == 0:
        return False
    if facts.success and not facts.friction_signals:
        return False
    if facts.error_message:
        return True
    if facts.friction_signals:
        return True
    return not facts.success or _looks_like_problem_summary(facts.last_progress_summary)


def _build_report_llm() -> Any | None:
    """构建使用 FAST_MODEL 的报告分析 LLM。

    报告分析不绑定具体 persona，使用默认模型预设（无预设时 env 兜底）。
    """
    from backend.stores import get_entity_store

    cfg = resolve_runtime_model(None, get_entity_store())
    model_name = cfg.fast_model_name or cfg.model_name

    if not model_name or not cfg.api_key or cfg.provider not in {"openai", "dashscope"}:
        return None

    if cfg.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=SecretStr(cfg.api_key),
            base_url=cfg.base_url or None,
        )

    if cfg.provider == "dashscope":
        from langchain_community.chat_models.tongyi import ChatTongyi

        return ChatTongyi(
            model=model_name,
            api_key=SecretStr(cfg.api_key),
        )

    return None


def _build_agent_messages(facts: ReportFacts, record: RunRecord) -> list[Any]:
    """构建 Agent 输入消息：精简的结构化事实 + persona/task 信息。"""

    facts_payload = {
        "run": {
            "success": facts.success,
            "total_steps": facts.total_steps,
            "error_type": facts.error_type,
            "error_message": facts.error_message,
        },
        "persona": {
            "id": record.persona.id,
            "name": record.persona.name,
            "description": record.persona.description,
            "skill_level": record.persona.skill_level,
            "patience_level": record.persona.patience_level,
            "risk_preference": record.persona.risk_preference,
        },
        "task": {
            "id": record.task.id,
            "name": record.task.name,
            "description": record.task.description,
            "success_criteria": record.task.success_criteria,
        },
        "facts": {
            "fallback_conclusion": facts.conclusion,
            "friction_signals": facts.friction_signals,
            "friction_issues": [issue.model_dump(mode="json") for issue in facts.friction_issues],
            "first_issue_step": facts.first_issue_step,
            "first_issue_summary": facts.first_issue_summary,
            "first_issue_error": facts.first_issue_error,
            "wait_observation_summary": facts.wait_observation_summary,
            "persona_impact": facts.persona_impact,
            "last_progress_summary": facts.last_progress_summary,
        },
        "step_summary": facts.step_action_summary,
    }

    return [
        SystemMessage(content=REPORT_ANALYSIS_PROMPT),
        HumanMessage(content=json.dumps(facts_payload, ensure_ascii=False, indent=2)),
    ]


def _generate_report_analysis(facts: ReportFacts, record: RunRecord) -> dict[str, Any]:
    """调用 FAST_MODEL 生成报告语义层（同步）。"""

    try:
        llm = _build_report_llm()
        if llm is None:
            return {}
        messages = _build_agent_messages(facts, record)
        response = llm.invoke(messages)
    except Exception:
        # _build_report_llm 现会做 DB 读（resolve_runtime_model），DB 故障时降级为无 LLM 报告而非击溃报告
        return {}

    response_text = _extract_message_text(response)
    return _parse_report_analysis(response_text)


async def _generate_report_analysis_async(facts: ReportFacts, record: RunRecord) -> dict[str, Any]:
    """调用 FAST_MODEL 生成报告语义层（异步）。"""

    try:
        llm = _build_report_llm()
        if llm is None:
            return {}
        messages = _build_agent_messages(facts, record)
        response = await llm.ainvoke(messages)
    except Exception:
        return {}

    response_text = _extract_message_text(response)
    return _parse_report_analysis(response_text)


# ============================ 事实提取辅助函数 ============================ #


def _build_conclusion(
    record: RunRecord,
    steps: list[StepLog],
    success: bool,
    friction_signals: list[str],
    last_progress_summary: str,
) -> ReportConclusion:
    if record.error_message:
        return "fix"
    if not steps:
        return "fix"
    if not success:
        return "fix"
    if friction_signals or _looks_like_problem_summary(last_progress_summary):
        return "optimize"
    return "keep"


def _find_first_issue_step(steps: list[StepLog]) -> StepLog | None:
    for step in steps:
        if step.validation_result.detected_error or step.validation_result.friction_signals:
            return step
    return None


def _build_wait_observation_summary(steps: list[StepLog]) -> str | None:
    wait_steps = [step for step in steps if step.wait_observation_status]
    if not wait_steps:
        return None

    descriptions = []
    for step in wait_steps:
        descriptions.append(
            f"第 {step.step_index} 步等待观察 {step.wait_observation_observations or 0} 次，"
            f"累计等待 {step.wait_observation_elapsed_ms or 0}ms，"
            f"最终状态为 {step.wait_observation_status}，"
            f"终止判断为 {step.wait_observation_terminal_decision or '无'}，"
            f"原因：{step.wait_observation_reason or '无'}"
        )
    return "；".join(descriptions) + "。"


def _build_persona_impact(
    record: RunRecord,
    friction_signals: list[str],
    success: bool,
) -> str | None:
    persona = record.persona
    if not friction_signals and success:
        return None

    risk_explanations: list[str] = []
    if persona.skill_level == "newbie":
        risk_explanations.append("对页面术语、流程切换和完成态提示更敏感")
    if persona.patience_level == "low" or "repeated_wait" in friction_signals or "stuck_page" in friction_signals:
        risk_explanations.append("在等待或状态不明确时更容易怀疑流程是否已完成")
    if persona.risk_preference == "low" and "repeated_action_target" in friction_signals:
        risk_explanations.append("倾向保守操作，遇到不确定按钮时更容易反复尝试同一路径")
    if "off_track_navigation" in friction_signals:
        risk_explanations.append("在主路径提示不够清晰时更容易偏离任务目标")

    if not risk_explanations:
        return None

    return f"对于 persona「{persona.name}」，这次问题更容易出现，因为该类用户{'; '.join(risk_explanations)}。"


# ============================ Agent 输出解析 ============================ #


def _extract_message_text(response: Any) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _parse_report_analysis(text: str) -> dict[str, Any]:
    if not text:
        return {}

    # Strip markdown code fences that LLMs frequently wrap around JSON
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.index("\n") if "\n" in stripped else -1
        if first_newline >= 0:
            stripped = stripped[first_newline + 1:]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
        stripped = stripped.strip()

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return {}

    if not isinstance(payload, dict):
        return {}

    conclusion = payload.get("conclusion")
    normalized: dict[str, Any] = {
        "summary": payload.get("summary", ""),
        "conclusion": conclusion if conclusion in CONCLUSION_SEVERITY_ORDER else None,
        "key_findings": _dedupe_text_items(payload.get("key_findings", [])),
        "next_recommendations": _dedupe_text_items(
            payload.get("next_recommendations", []),
            limit=RECOMMENDATION_LIMIT,
        ),
    }
    return normalized


# ============================ 通用工具函数 ============================ #


def _merge_conclusion(
    fallback_conclusion: ReportConclusion,
    generated_conclusion: Any,
) -> ReportConclusion:
    if generated_conclusion not in CONCLUSION_SEVERITY_ORDER:
        return fallback_conclusion
    if CONCLUSION_SEVERITY_ORDER[generated_conclusion] < CONCLUSION_SEVERITY_ORDER[fallback_conclusion]:
        return fallback_conclusion
    return generated_conclusion


def _dedupe_text_items(items: Any, limit: int | None = None) -> list[str]:
    if not isinstance(items, list):
        return []

    deduped: list[str] = []
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        if text not in deduped:
            deduped.append(text)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def _looks_like_problem_summary(summary: str) -> bool:
    keywords = ("失败", "卡住", "偏航", "仍无进展", "错误", "异常", "中断")
    return any(keyword in summary for keyword in keywords)


def _collect_friction_signals(steps: list[StepLog]) -> list[str]:
    collected: list[str] = []
    for step in steps:
        for signal in step.validation_result.friction_signals:
            if signal and signal not in collected:
                collected.append(signal)
    return collected


# ============================ 关键截图提取 ============================ #


def _extract_key_screenshots(steps: list[StepLog], success: bool) -> list[KeyScreenshot]:
    """从步骤日志中提取关键截图，按重要事件筛选。"""

    if not steps:
        return []

    screenshots: list[KeyScreenshot] = []
    seen_paths: set[str] = set()

    def _add(label: str, step_index: int, path: str, source: str) -> None:
        if path and path not in seen_paths:
            seen_paths.add(path)
            screenshots.append(KeyScreenshot(label=label, step_index=step_index, path=path, source=source))

    # 第一步起始页面
    first = steps[0]
    _add("起始页面", first.step_index, first.observed_page_state.screenshot_path, "before_action")

    # 首个报错步骤
    for step in steps:
        if step.validation_result.detected_error:
            _add("首次报错页面", step.step_index, step.observed_page_state.screenshot_path, "before_action")
            break

    # 首个恢复相关摩擦信号步骤
    recovery_signals = {"action_failed", "recovery_candidate", "page_error"}
    for step in steps:
        if any(s in recovery_signals for s in step.validation_result.friction_signals):
            _add("恢复尝试起点", step.step_index, step.observed_page_state.screenshot_path, "before_action")
            break

    # 首个异常等待观察截图
    for step in steps:
        if step.wait_observation_status == "abnormal_stuck" and step.wait_observation_traces:
            for trace in step.wait_observation_traces:
                trace_path = trace.get("screenshot_path")
                if trace_path:
                    _add("异常等待状态", step.step_index, trace_path, "wait_observation")
                    break
            break

    # 成功时最后一步确认截图
    if success:
        last = steps[-1]
        _add("任务成功确认", last.step_index, last.post_action_page_state.screenshot_path, "after_action")

    return screenshots


# ============================ 步骤序列化 ============================ #


def _serialize_step(step: StepLog) -> dict[str, Any]:
    return {
        "step_index": step.step_index,
        "before_page_state": step.observed_page_state.model_dump(mode="json"),
        "action": step.decided_action.action,
        "payload": step.decided_action.payload.model_dump(mode="json"),
        "action_reason": step.decided_action.reason,
        "execution_success": step.execution_result.success,
        "execution_detail": step.execution_result.detail,
        "execution_error_message": step.execution_result.error_message,
        "validation_status": step.validation_result.status,
        "validation_summary": step.validation_result.progress_summary,
        "validation_friction_signals": step.validation_result.friction_signals,
        "detected_success": step.validation_result.detected_success,
        "detected_error": step.validation_result.detected_error,
        "after_page_state": step.post_action_page_state.model_dump(mode="json"),
        "wait_observation_status": step.wait_observation_status,
        "wait_observation_reason": step.wait_observation_reason,
        "wait_observation_observations": step.wait_observation_observations,
        "wait_observation_elapsed_ms": step.wait_observation_elapsed_ms,
        "wait_observation_timeout_ms": step.wait_observation_timeout_ms,
        "wait_observation_terminal_decision": step.wait_observation_terminal_decision,
        "wait_observation_traces": step.wait_observation_traces,
        "retrieval_context": [item.model_dump(mode="json") for item in step.retrieval_context],
    }

from __future__ import annotations

# ============================ 报告生成模块 ============================ #
# 使用技术栈: Python / Pydantic / LangChain
# 模块功能: 基于步骤日志整理最终 run 报告，并按本次 run 的证据生成详细报告与建议
# 模块数据流: RunRecord + StepLog[] -> RunReport
# 模块接口说明: build_run_report() 返回最终结构化报告, run 结束直接返回报告

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from backend.ai_api.provider_router import get_model_router
from backend.prompt.report import RECOMMENDATION_SYSTEM_PROMPT
from backend.schemas.run_schemas import ReportConclusion, RunRecord, RunReport, StepLog

RECOMMENDATION_LIMIT = 10
CONCLUSION_SEVERITY_ORDER: dict[ReportConclusion, int] = {
    "keep": 0,
    "optimize": 1,
    "fix": 2,
}


def build_run_report(record: RunRecord, steps: list[StepLog]) -> RunReport:
    """生成当前 run 的结构化报告。"""

    success = bool(steps and steps[-1].validation_result.detected_success)
    last_progress_summary = steps[-1].validation_result.progress_summary if steps else "任务未执行任何步骤。"
    friction_signals = _collect_friction_signals(steps)
    conclusion = _build_conclusion(record, steps, success, friction_signals, last_progress_summary)
    key_findings = _build_base_key_findings(record, steps, success, conclusion, friction_signals, last_progress_summary)

    generated_key_findings: list[str] = []
    recommendations: list[str] = []
    if _should_generate_detailed_report(record, steps, success, friction_signals, last_progress_summary):
        analysis = _generate_report_analysis(
            record=record,
            steps=steps,
            success=success,
            friction_signals=friction_signals,
            last_progress_summary=last_progress_summary,
            fallback_conclusion=conclusion,
        )
        conclusion = _merge_conclusion(conclusion, analysis.get("conclusion"))
        generated_key_findings = _dedupe_text_items(analysis.get("key_findings", []))
        recommendations = _dedupe_text_items(analysis.get("next_recommendations", []), limit=RECOMMENDATION_LIMIT)

    final_key_findings = _dedupe_text_items([*key_findings, *generated_key_findings])

    return RunReport(
        run_id=record.run_id,
        status="succeeded" if success else "failed",
        summary=last_progress_summary,
        success=success,
        conclusion=conclusion,
        persona=record.persona,
        task=record.task,
        total_steps=len(steps),
        friction_signals=friction_signals,
        key_findings=final_key_findings,
        next_recommendations=recommendations,
        error_type=record.error_type,
        error_message=record.error_message,
    )


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


def _build_base_key_findings(
    record: RunRecord,
    steps: list[StepLog],
    success: bool,
    conclusion: ReportConclusion,
    friction_signals: list[str],
    last_progress_summary: str,
) -> list[str]:
    findings = [
        f"共执行 {len(steps)} 步。",
        f"最终状态为 {'成功' if success else '失败'}。",
        f"最终结论为 {conclusion}。",
        f"最后一步判定：{last_progress_summary}",
    ]

    if friction_signals:
        findings.append(f"检测到摩擦信号: {', '.join(friction_signals)}。")

    wait_finding = _build_wait_observation_finding(steps)
    if wait_finding:
        findings.append(wait_finding)

    first_issue_step = _find_first_issue_step(steps)
    if first_issue_step is not None:
        findings.append(
            f"首次明显问题出现在第 {first_issue_step.step_index} 步：{first_issue_step.validation_result.progress_summary}"
        )
        if first_issue_step.execution_result.error_message:
            findings.append(f"对应执行错误：{first_issue_step.execution_result.error_message}")

    if record.error_message:
        findings.append(f"运行过程中出现{_format_error_type(record.error_type)}：{record.error_message}")

    persona_finding = _build_persona_impact_finding(record, friction_signals, success)
    if persona_finding:
        findings.append(persona_finding)

    return findings


def _format_error_type(error_type: str | None) -> str:
    if error_type == "model_error":
        return "模型调用错误"
    return "系统异常中断"


def _build_wait_observation_finding(steps: list[StepLog]) -> str:
    wait_steps = [step for step in steps if step.wait_observation_status]
    if not wait_steps:
        return ""

    descriptions = []
    for step in wait_steps:
        descriptions.append(
            f"第 {step.step_index} 步等待观察 {step.wait_observation_observations or 0} 次，"
            f"最终状态为 {step.wait_observation_status}，原因：{step.wait_observation_reason or '无'}"
        )
    return "；".join(descriptions) + "。"


def _build_persona_impact_finding(
    record: RunRecord,
    friction_signals: list[str],
    success: bool,
) -> str:
    persona = record.persona
    if not friction_signals and success:
        return ""

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
        return ""

    return f"对于 persona「{persona.name}」，这次问题更容易出现，因为该类用户{'; '.join(risk_explanations)}。"


def _should_generate_detailed_report(
    record: RunRecord,
    steps: list[StepLog],
    success: bool,
    friction_signals: list[str],
    last_progress_summary: str,
) -> bool:
    if not steps:
        return False
    if success and not friction_signals:
        return False
    if record.error_message:
        return True
    if friction_signals:
        return True
    return not success or _looks_like_problem_summary(last_progress_summary)


def _generate_report_analysis(
    record: RunRecord,
    steps: list[StepLog],
    success: bool,
    friction_signals: list[str],
    last_progress_summary: str,
    fallback_conclusion: ReportConclusion,
) -> dict[str, Any]:
    llm = _build_recommendation_llm()
    if llm is None:
        return {}

    prompt_payload = _build_recommendation_payload(
        record,
        steps,
        success,
        friction_signals,
        last_progress_summary,
        fallback_conclusion,
    )
    messages = [
        SystemMessage(content=RECOMMENDATION_SYSTEM_PROMPT),
        HumanMessage(content=json.dumps(prompt_payload, ensure_ascii=False, indent=2)),
    ]

    try:
        response = llm.invoke(messages)
    except Exception:
        return {}

    response_text = _extract_message_text(response)
    return _parse_report_analysis(response_text)


def _build_recommendation_llm() -> Any | None:
    router = get_model_router()
    if not router.model_name or router.model_provider not in {"openai", "dashscope"}:
        return None

    if router.model_provider == "openai":
        if not router.api_key:
            return None
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=router.model_name,
            api_key=SecretStr(router.api_key),
            base_url=router.base_url or None,
        )

    if router.model_provider == "dashscope":
        if not router.api_key:
            return None
        from langchain_community.chat_models.tongyi import ChatTongyi

        return ChatTongyi(
            model=router.model_name,
            api_key=SecretStr(router.api_key),
        )

    return None


def _build_recommendation_payload(
    record: RunRecord,
    steps: list[StepLog],
    success: bool,
    friction_signals: list[str],
    last_progress_summary: str,
    fallback_conclusion: ReportConclusion,
) -> dict[str, Any]:
    return {
        "run": {
            "run_id": record.run_id,
            "status": record.status,
            "success": success,
            "error_type": record.error_type,
            "error_message": record.error_message,
            "step_count": len(steps),
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
            "start_url": record.task.start_url,
            "success_criteria": record.task.success_criteria,
            "max_steps": record.task.max_steps,
            "allowed_actions": record.task.allowed_actions,
            "risk_level": record.task.risk_level,
            "destructive_action_allowed": record.task.destructive_action_allowed,
        },
        "signals": {
            "friction_signals": friction_signals,
            "last_progress_summary": last_progress_summary,
            "problem_summary": _summarize_problem_pattern(steps),
            "fallback_conclusion": fallback_conclusion,
        },
        "all_steps": [_serialize_step(step) for step in steps],
    }


def _serialize_step(step: StepLog) -> dict[str, Any]:
    return {
        "step_index": step.step_index,
        "page_url": step.observed_page_state.current_url,
        "page_title": step.observed_page_state.title,
        "visible_text_summary": step.observed_page_state.visible_text_summary,
        "page_errors": step.observed_page_state.error_messages,
        "action": step.decided_action.action,
        "target": step.decided_action.target,
        "action_reason": step.decided_action.reason,
        "execution_success": step.execution_result.success,
        "execution_detail": step.execution_result.detail,
        "execution_error_message": step.execution_result.error_message,
        "validation_status": step.validation_result.status,
        "validation_summary": step.validation_result.progress_summary,
        "validation_friction_signals": step.validation_result.friction_signals,
        "detected_success": step.validation_result.detected_success,
        "detected_error": step.validation_result.detected_error,
        "wait_observation_status": step.wait_observation_status,
        "wait_observation_reason": step.wait_observation_reason,
        "wait_observation_observations": step.wait_observation_observations,
        "wait_observation_traces": step.wait_observation_traces,
    }


def _summarize_problem_pattern(steps: list[StepLog]) -> dict[str, Any]:
    friction_counts: dict[str, int] = {}
    problem_step_indexes: list[int] = []
    for step in steps:
        if step.validation_result.friction_signals or step.validation_result.detected_error:
            problem_step_indexes.append(step.step_index)
        for signal in step.validation_result.friction_signals:
            friction_counts[signal] = friction_counts.get(signal, 0) + 1

    return {
        "friction_counts": friction_counts,
        "problem_step_indexes": problem_step_indexes,
        "last_actions": [step.decided_action.action for step in steps[-3:]],
        "last_targets": [step.decided_action.target for step in steps[-3:]],
        "last_validation_summaries": [step.validation_result.progress_summary for step in steps[-3:]],
    }


def _extract_message_text(response: Any) -> str:
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _parse_report_analysis(text: str) -> dict[str, Any]:
    if not text:
        return {}

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}

    if not isinstance(payload, dict):
        return {}

    conclusion = payload.get("conclusion")
    normalized: dict[str, Any] = {
        "conclusion": conclusion if conclusion in CONCLUSION_SEVERITY_ORDER else None,
        "key_findings": _dedupe_text_items(payload.get("key_findings", [])),
        "next_recommendations": _dedupe_text_items(
            payload.get("next_recommendations", []),
            limit=RECOMMENDATION_LIMIT,
        ),
    }
    return normalized


def _find_first_issue_step(steps: list[StepLog]) -> StepLog | None:
    for step in steps:
        if step.validation_result.detected_error or step.validation_result.friction_signals:
            return step
    return None


def _merge_conclusion(
    fallback_conclusion: ReportConclusion,
    generated_conclusion: Any,
) -> ReportConclusion:
    if generated_conclusion not in CONCLUSION_SEVERITY_ORDER:
        return fallback_conclusion
    generated = generated_conclusion
    if CONCLUSION_SEVERITY_ORDER[generated] < CONCLUSION_SEVERITY_ORDER[fallback_conclusion]:
        return fallback_conclusion
    return generated


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

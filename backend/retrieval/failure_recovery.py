from __future__ import annotations

from dataclasses import dataclass

from backend.schemas.run_schemas import (
    ActionInput,
    ActionName,
    AbandonPayload,
    NavigateActionPayload,
    PressActionPayload,
    RetrievedContextItem,
    StepLog,
    Task,
)
from backend.stores.entity_store_protocol import EntityStore


@dataclass(frozen=True)
class FailureCaseSeed:
    error_pattern: str
    symptom: str
    recovery_action: ActionName
    recovery_description: str
    keywords: tuple[str, ...]


_FAILURE_CASES: tuple[FailureCaseSeed, ...] = (
    FailureCaseSeed(
        error_pattern="repeated_action_target",
        symptom="同一动作重复执行多次仍无进展",
        recovery_action="navigate",
        recovery_description="回到任务起始页重新进入主流程",
        keywords=("重复", "无进展", "重复点击", "重复填写"),
    ),
    FailureCaseSeed(
        error_pattern="stuck_page",
        symptom="页面连续多步无变化且没有明确下一步入口",
        recovery_action="navigate",
        recovery_description="回到任务起始页重新进入主流程",
        keywords=("无响应", "无变化", "卡住", "停滞"),
    ),
    FailureCaseSeed(
        error_pattern="off_track_navigation",
        symptom="连续多步跳转后偏离任务主路径",
        recovery_action="navigate",
        recovery_description="回到任务起始页重新进入主流程",
        keywords=("偏离", "跳转", "偏航", "非目标页"),
    ),
    FailureCaseSeed(
        error_pattern="repeated_wait",
        symptom="连续等待多次仍无进展",
        recovery_action="click",
        recovery_description="尝试点击页面上最近出现的主路径按钮",
        keywords=("等待", "无进展", "超时"),
    ),
    FailureCaseSeed(
        error_pattern="page_error",
        symptom="页面出现错误提示或异常状态",
        recovery_action="press",
        recovery_description="按 Escape 关闭弹窗或错误提示后重新观察",
        keywords=("错误", "弹窗", "异常", "报错"),
    ),
)


def retrieve_failure_cases(
    friction_signals: list[str],
    step_logs: list[StepLog],
    *,
    entity_store: EntityStore | None = None,
) -> list[RetrievedContextItem]:
    """根据当前摩擦信号与执行历史，检索相似失败案例与恢复建议。

    当 entity_store 提供时，优先从其中查询真实 failure_case 条目。
    空库或提供 None 时回退到硬编码种子。
    """

    if not friction_signals and not step_logs:
        return []

    seeds = list(_FAILURE_CASES)
    if entity_store is not None:
        seeds = _merge_failure_case_seeds(seeds, entity_store)

    query_text = _build_failure_query(friction_signals, step_logs)

    matched: list[tuple[int, FailureCaseSeed | _EntityFailureCase]] = []
    for seed in seeds:
        if seed.error_pattern in friction_signals:
            matched.append((10, seed))
            continue
        keyword_hits = sum(1 for kw in seed.keywords if kw in query_text)
        if keyword_hits > 0:
            matched.append((keyword_hits, seed))

    matched.sort(key=lambda item: -item[0])

    return [
        _to_retrieved_item(seed)
        for _, seed in matched
    ]


def choose_recovery_action(
    task: Task,
    friction_signals: list[str],
    step_logs: list[StepLog],
    recovery_history: list[dict],
    *,
    entity_store: EntityStore | None = None,
) -> ActionInput:
    """根据失败案例检索结果与恢复历史，选择受控恢复动作。

    当 entity_store 提供时，从真实知识库读取失败案例，合并硬编码种子后择优。
    """

    attempted_patterns = {entry.get("error_pattern") for entry in recovery_history}

    seeds = list(_FAILURE_CASES)
    if entity_store is not None:
        seeds = _merge_failure_case_seeds(seeds, entity_store)

    query_text = _build_failure_query(friction_signals, step_logs)
    candidates: list[tuple[int, FailureCaseSeed | _EntityFailureCase]] = []
    for seed in seeds:
        if seed.error_pattern in friction_signals:
            candidates.append((10, seed))
        elif any(kw in query_text for kw in seed.keywords):
            candidates.append((1, seed))

    candidates.sort(key=lambda item: -item[0])

    for _, seed in candidates:
        if seed.error_pattern in attempted_patterns:
            continue
        return _build_recovery_action(task, seed)

    navigate_attempted = any(entry.get("action") == "navigate" for entry in recovery_history)
    if not navigate_attempted:
        return ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=task.start_url),
            reason="所有针对性恢复已尝试，回到起始页重新开始。",
        )

    return ActionInput(
        action="abandon",
        payload=AbandonPayload(reason="所有恢复动作均已尝试且无效，终止本次运行。"),
        reason="恢复路径耗尽，放弃任务。",
    )


# ============================ Helpers ============================ #


@dataclass(frozen=True)
class _EntityFailureCase:
    """轻量适配类型，将 entity_store 的 FailureCase 条目桥接到 FailureCaseSeed 打分逻辑。"""
    error_pattern: str
    symptom: str
    recovery_action: ActionName
    recovery_description: str
    keywords: tuple[str, ...]
    source_ref: str


def _merge_failure_case_seeds(
    seeds: list[FailureCaseSeed],
    entity_store: EntityStore,
) -> list[FailureCaseSeed | _EntityFailureCase]:
    """将 entity_store 中的失败案例条目合并到硬编码种子列表中。"""
    try:
        items = entity_store.list_knowledge_items(source_type="failure_case")
    except Exception:
        return seeds

    converted = [
        _EntityFailureCase(
            error_pattern=item.source_ref or item.id,
            symptom=item.title,
            recovery_action="navigate",
            recovery_description=item.content,
            keywords=tuple(item.keywords or ()),
            source_ref=item.source_ref or f"entity:{item.id}",
        )
        for item in items
    ]
    return seeds + converted  # type: ignore[return-value]


def _to_retrieved_item(seed: FailureCaseSeed | _EntityFailureCase) -> RetrievedContextItem:
    """统一构建 RetrievedContextItem。"""
    symptom = seed.symptom
    recovery_action = seed.recovery_action
    recovery_desc = seed.recovery_description
    return RetrievedContextItem(
        source_type="failure_case",
        title=f"失败案例: {symptom}",
        content=f"症状: {symptom}。建议恢复动作: {recovery_action} — {recovery_desc}。",
        source_ref=getattr(seed, "source_ref", f"seed:failure_recovery:{seed.error_pattern}"),
    )


def _build_recovery_action(task: Task, seed: FailureCaseSeed | _EntityFailureCase) -> ActionInput:
    if seed.recovery_action == "navigate":
        return ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=task.start_url),
            reason=f"恢复: {seed.recovery_description}。",
        )
    if seed.recovery_action == "press":
        return ActionInput(
            action="press",
            payload=PressActionPayload(key="Escape"),
            reason=f"恢复: {seed.recovery_description}。",
        )
    if seed.recovery_action == "click":
        return ActionInput(
            action="navigate",
            payload=NavigateActionPayload(url=task.start_url),
            reason=f"恢复: 无明确可点击目标，{seed.recovery_description}。",
        )
    return ActionInput(
        action="navigate",
        payload=NavigateActionPayload(url=task.start_url),
        reason=f"恢复: {seed.recovery_description}。",
    )


def _build_failure_query(friction_signals: list[str], step_logs: list[StepLog]) -> str:
    parts = list(friction_signals)
    if step_logs:
        last = step_logs[-1]
        parts.append(last.decided_action.action)
        if last.execution_result.error_message:
            parts.append(last.execution_result.error_message)
        if last.validation_result.progress_summary:
            parts.append(last.validation_result.progress_summary)
    return " ".join(parts).lower()

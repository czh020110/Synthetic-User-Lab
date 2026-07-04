from __future__ import annotations

from dataclasses import dataclass

from backend.schemas.run_schemas import Persona, RetrievedContextItem, RetrievalSourceType, Task
from backend.stores.entity_store_protocol import EntityStore


@dataclass(frozen=True)
class RetrievalSeed:
    source_type: RetrievalSourceType
    title: str
    content: str
    keywords: tuple[str, ...]
    source_ref: str


_SOURCE_TYPES: tuple[RetrievalSourceType, RetrievalSourceType] = ("product_knowledge", "failure_case")

_SEEDS: tuple[RetrievalSeed, ...] = (
    RetrievalSeed(
        source_type="product_knowledge",
        title="表单完成标准",
        content="页面明确显示任务完成状态、成功卡片可见且表单已隐藏时，可判定为完成。",
        keywords=("任务完成状态", "成功卡片", "表单已隐藏", "完成"),
        source_ref="seed:product_knowledge:success_criteria",
    ),
    RetrievalSeed(
        source_type="product_knowledge",
        title="正常等待提示",
        content="当页面显示正在处理、请稍候或加载中时，优先等待后端处理结束，再继续下一步。",
        keywords=("正在处理", "请稍候", "加载中", "等待"),
        source_ref="seed:product_knowledge:waiting_state",
    ),
    RetrievalSeed(
        source_type="failure_case",
        title="重复点击无进展",
        content="同一按钮重复点击多次仍没有变化时，不要继续重复操作，转向受控恢复路径。",
        keywords=("重复点击", "无进展", "无变化", "恢复路径"),
        source_ref="seed:failure_case:repeated_click",
    ),
    RetrievalSeed(
        source_type="failure_case",
        title="页面无响应恢复",
        content="页面连续多步无变化且没有明确下一步入口时，先回到 start_url，再重新进入主流程。",
        keywords=("无响应", "无变化", "start_url", "主流程", "恢复"),
        source_ref="seed:failure_case:stuck_page",
    ),
)


def build_retrieval_context(
    persona: Persona,
    task: Task,
    *,
    entity_store: EntityStore | None = None,
    limit_per_type: int = 2,
) -> list[RetrievedContextItem]:
    query = _build_query_text(persona, task)
    contexts: list[RetrievedContextItem] = []

    for source_type in _SOURCE_TYPES:
        # Get seeds for this source_type only
        type_seeds = [s for s in _SEEDS if s.source_type == source_type]
        if entity_store is not None:
            type_seeds = _merge_entity_store_items(type_seeds, entity_store, source_type)
        ranked = _rank_seeds(query, type_seeds)
        for seed in ranked[:limit_per_type]:
            contexts.append(
                RetrievedContextItem(
                    source_type=seed.source_type,
                    title=seed.title,
                    content=seed.content,
                    source_ref=seed.source_ref,
                )
            )
    return contexts


def render_retrieval_context(items: list[RetrievedContextItem]) -> str:
    if not items:
        return "暂无可用检索上下文。"

    return "\n".join(
        f"{index}. [{item.source_type}] {item.title}: {item.content}"
        for index, item in enumerate(items, start=1)
    )


def _merge_entity_store_items(
    seeds: list[RetrievalSeed],
    entity_store: EntityStore,
    source_type: RetrievalSourceType,
) -> list[RetrievalSeed]:
    """将 entity_store 中的真实条目与硬编码种子合并，真实条目排在种子前面。"""
    try:
        items = entity_store.list_knowledge_items(source_type=source_type)
    except Exception:
        return seeds

    converted = [
        RetrievalSeed(
            source_type=item.source_type,
            title=item.title,
            content=item.content,
            keywords=tuple(item.keywords or ()),
            source_ref=item.source_ref or f"entity:{item.id}",
        )
        for item in items
    ]
    # 真实条目排在前面，确保它们不因 limit_per_type 截断而被跳过
    return converted + seeds  # type: ignore[return-value]


def _build_query_text(persona: Persona, task: Task) -> str:
    parts = [
        persona.name,
        persona.description,
        persona.skill_level,
        persona.patience_level,
        persona.risk_preference,
        task.name,
        task.description,
        task.start_url,
        task.risk_level,
        *(task.success_criteria or []),
    ]
    return "\n".join(part for part in parts if part).lower()


def _rank_seeds(query: str, seeds: list[RetrievalSeed]) -> list[RetrievalSeed]:
    scored = sorted(
        ((_score_seed(query, seed), seed) for seed in seeds),
        key=lambda item: (-item[0], item[1].title),
    )
    return [seed for _score, seed in scored]


def _score_seed(query: str, seed: RetrievalSeed) -> int:
    """按关键词命中数打分；命中关键词得 1 分；标题/内容包含关键词也予加权。"""
    score = 0
    query_lower = query.lower()
    for keyword in seed.keywords:
        kw_lower = keyword.lower()
        if kw_lower in query_lower:
            score += 1
        if kw_lower in seed.content.lower() or kw_lower in seed.title.lower():
            score += 1
    return score

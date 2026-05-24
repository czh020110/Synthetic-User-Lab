from __future__ import annotations

from dataclasses import dataclass

from backend.schemas.run_schemas import Persona, RetrievedContextItem, RetrievalSourceType, Task


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


def build_retrieval_context(persona: Persona, task: Task, *, limit_per_type: int = 2) -> list[RetrievedContextItem]:
    query = _build_query_text(persona, task)
    contexts: list[RetrievedContextItem] = []
    for source_type in _SOURCE_TYPES:
        ranked = _rank_seeds(query, source_type)
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


def _rank_seeds(query: str, source_type: RetrievalSourceType) -> list[RetrievalSeed]:
    candidates = [seed for seed in _SEEDS if seed.source_type == source_type]
    scored = sorted(
        ((sum(1 for keyword in seed.keywords if keyword.lower() in query), seed) for seed in candidates),
        key=lambda item: (-item[0], item[1].title),
    )
    return [seed for _score, seed in scored]

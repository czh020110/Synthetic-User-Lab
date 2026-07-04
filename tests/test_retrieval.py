from __future__ import annotations

from backend.graph.demo_run_graph import build_demo_persona, build_demo_task
from backend.retrieval import build_retrieval_context, render_retrieval_context
from backend.stores.in_memory_entity_store import InMemoryEntityStore


def test_build_retrieval_context_returns_product_knowledge_and_failure_cases() -> None:
    persona = build_demo_persona()
    task = build_demo_task("http://testserver")

    items = build_retrieval_context(persona, task)

    assert items
    assert any(item.source_type == "product_knowledge" for item in items)
    assert any(item.source_type == "failure_case" for item in items)
    assert any(item.title == "表单完成标准" for item in items)
    assert any(item.title == "页面无响应恢复" for item in items)


def test_render_retrieval_context_formats_short_text() -> None:
    persona = build_demo_persona()
    task = build_demo_task("http://testserver")
    items = build_retrieval_context(persona, task)

    rendered = render_retrieval_context(items)
    lines = rendered.splitlines()

    assert len(lines) == len(items)
    assert lines[0].startswith("1. [")
    assert all(": " in line for line in lines)
    assert any("[product_knowledge]" in line for line in lines)
    assert any("[failure_case]" in line for line in lines)
    assert "表单完成标准" in rendered
    assert "页面无响应恢复" in rendered


def test_build_retrieval_context_without_entity_store_falls_back_to_seeds() -> None:
    persona = build_demo_persona()
    task = build_demo_task("http://testserver")

    # entity_store=None should still work using hard-coded seeds only
    items = build_retrieval_context(persona, task, entity_store=None)
    assert len(items) > 0
    # All items must be from seeds
    for item in items:
        assert item.source_ref.startswith("seed:")


def test_build_retrieval_context_with_empty_entity_store_falls_back() -> None:
    persona = build_demo_persona()
    task = build_demo_task("http://testserver")

    entity_store = InMemoryEntityStore()
    items = build_retrieval_context(persona, task, entity_store=entity_store)

    assert len(items) > 0
    # Should still get seed items when store is empty
    assert any(item.source_ref.startswith("seed:") for item in items)


def test_build_retrieval_context_with_real_product_knowledge() -> None:
    persona = build_demo_persona()
    task = build_demo_task("http://testserver")

    entity_store = InMemoryEntityStore()
    from backend.schemas.knowledge_schemas import KnowledgeItem
    item = KnowledgeItem(
        source_type="product_knowledge",
        title="Demo 注册完成条件",
        content="注册成功后页面显示绿色提示卡。",
        keywords=["注册", "完成", "提示卡"],
        source_ref="test:pk:register",
    )

    entity_store.create_knowledge_item(item)

    result = build_retrieval_context(persona, task, entity_store=entity_store)
    # Should include the real product knowledge
    assert any(it.source_ref == "test:pk:register" for it in result)


def test_build_retrieval_context_source_type_filter() -> None:
    """Empty entity_store returns both product_knowledge and failure_case from seeds."""
    persona = build_demo_persona()
    task = build_demo_task("http://testserver")

    entity_store = InMemoryEntityStore()
    items = build_retrieval_context(persona, task, entity_store=entity_store)

    has_product = any(i.source_type == "product_knowledge" for i in items)
    has_failure = any(i.source_type == "failure_case" for i in items)
    assert has_product
    assert has_failure

from __future__ import annotations

from backend.graph.demo_run_graph import build_demo_persona, build_demo_task
from backend.retrieval import build_retrieval_context, render_retrieval_context


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

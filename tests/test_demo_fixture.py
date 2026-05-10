from pathlib import Path

from backend.graph.demo_run_graph import build_demo_task


def test_demo_site_contains_waiting_loading_state() -> None:
    html = Path("backend/fixtures/demo_site/index.html").read_text(encoding="utf-8")

    assert "loading-card" in html
    assert "正在注册" in html
    assert "setTimeout" in html
    assert "10000" in html
    assert "success-card" in html


def test_demo_task_does_not_hint_waiting_delay() -> None:
    task = build_demo_task("http://127.0.0.1:8765")

    assert "10秒" not in task.description
    assert "正在注册" not in task.description
    assert "注册中" not in task.description

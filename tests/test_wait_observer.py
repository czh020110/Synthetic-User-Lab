from __future__ import annotations

import asyncio

from backend.graph.wait_observer import WaitObservationDecision, WaitObservationOptions, observe_until_ready
from backend.schemas.run_schemas import ObservedPageState


class FakePage:
    def __init__(self) -> None:
        self.wait_calls: list[int] = []

    async def wait_for_timeout(self, timeout: int) -> None:
        self.wait_calls.append(timeout)


def make_page_state(*, url: str = "http://127.0.0.1:8765/demo/index.html", text: str = "页面状态") -> ObservedPageState:
    return ObservedPageState(
        current_url=url,
        title="demo",
        visible_text_summary=text,
        clickable_elements=[],
        form_fields=[],
        error_messages=[],
    )


async def observe_sequence(states: list[ObservedPageState]):
    iterator = iter(states)

    async def _observe(_page):
        del _page
        return next(iterator)

    return _observe


async def decision_sequence(decisions: list[WaitObservationDecision]):
    iterator = iter(decisions)

    async def _classify(_page_state, _elapsed_ms: int, _observations: int):
        del _page_state, _elapsed_ms, _observations
        return next(iterator)

    return _classify


def test_observe_until_ready_returns_success_after_model_detects_completion() -> None:
    page = FakePage()
    states = [
        make_page_state(text="状态 A"),
        make_page_state(text="状态 B"),
        make_page_state(text="状态 C"),
    ]
    decisions = [
        WaitObservationDecision(decision="continue_waiting", reason="仍在处理。"),
        WaitObservationDecision(decision="continue_waiting", reason="还没有下一步。"),
        WaitObservationDecision(decision="task_completed", reason="模型判断任务已经完成。"),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(interval_ms=1, timeout_ms=5),
        )

    result = asyncio.run(_run())

    assert result.status == "success"
    assert result.observations == 3
    assert result.reason == "模型判断任务已经完成。"
    assert len(result.traces) == 3
    assert result.traces[-1].decision == "task_completed"
    assert page.wait_calls == [1, 1]


def test_observe_until_ready_returns_actionable_after_model_detects_next_action() -> None:
    page = FakePage()
    states = [make_page_state(text="状态 A")]
    decisions = [WaitObservationDecision(decision="ready_for_next_action", reason="页面已有下一步入口。")]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(interval_ms=1, timeout_ms=5),
        )

    result = asyncio.run(_run())

    assert result.status == "actionable"
    assert result.observations == 1
    assert result.reason == "页面已有下一步入口。"
    assert page.wait_calls == []


def test_observe_until_ready_times_out_when_model_keeps_waiting() -> None:
    page = FakePage()
    states = [
        make_page_state(text="状态 A"),
        make_page_state(text="状态 B"),
        make_page_state(text="状态 C"),
    ]
    decisions = [
        WaitObservationDecision(decision="continue_waiting", reason="继续等待。"),
        WaitObservationDecision(decision="continue_waiting", reason="继续等待。"),
        WaitObservationDecision(decision="continue_waiting", reason="继续等待。"),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(interval_ms=1, timeout_ms=2),
        )

    result = asyncio.run(_run())

    assert result.status == "timeout"
    assert result.observations == 3
    assert result.reason == "等待超过 10 分钟，仍未出现可继续操作或完成状态。"

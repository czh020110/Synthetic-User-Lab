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

    async def _classify(_page_state, _elapsed_ms: int, _observations: int, _normal_remaining_ms: int, _abnormal_remaining_ms: int):
        del _page_state, _elapsed_ms, _observations, _normal_remaining_ms, _abnormal_remaining_ms
        return next(iterator)

    return _classify


def test_observe_until_ready_returns_success_after_normal_waiting() -> None:
    page = FakePage()
    states = [
        make_page_state(text="状态 A"),
        make_page_state(text="状态 B"),
        make_page_state(text="状态 C"),
    ]
    decisions = [
        WaitObservationDecision(decision="normal_waiting", reason="仍在正常处理中。", next_wait_ms=1000),
        WaitObservationDecision(decision="normal_waiting", reason="继续等待结果。", next_wait_ms=2000),
        WaitObservationDecision(decision="task_completed", reason="模型判断任务已经完成。", next_wait_ms=0),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(
                normal_timeout_ms=5000,
                abnormal_timeout_ms=3000,
                min_wait_ms=1,
                max_wait_ms=5000,
                default_wait_ms=1,
            ),
        )

    result = asyncio.run(_run())

    assert result.status == "success"
    assert result.observations == 3
    assert result.reason == "模型判断任务已经完成。"
    assert result.elapsed_ms == 3000
    assert result.timeout_ms == 5000
    assert result.terminal_decision == "task_completed"
    assert len(result.traces) == 3
    assert result.traces[0].next_wait_ms == 1000
    assert result.traces[1].next_wait_ms == 2000
    assert result.traces[-1].decision == "task_completed"
    assert page.wait_calls == [1000, 2000]


def test_observe_until_ready_returns_actionable() -> None:
    page = FakePage()
    states = [make_page_state(text="状态 A")]
    decisions = [WaitObservationDecision(decision="ready_for_next_action", reason="页面已有下一步入口。", next_wait_ms=0)]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(),
        )

    result = asyncio.run(_run())

    assert result.status == "actionable"
    assert result.observations == 1
    assert result.reason == "页面已有下一步入口。"
    assert result.elapsed_ms == 0
    assert result.terminal_decision == "ready_for_next_action"
    assert page.wait_calls == []


def test_observe_until_ready_returns_normal_timeout() -> None:
    page = FakePage()
    states = [
        make_page_state(text="状态 A"),
        make_page_state(text="状态 B"),
        make_page_state(text="状态 C"),
    ]
    decisions = [
        WaitObservationDecision(decision="normal_waiting", reason="继续正常等待。", next_wait_ms=2),
        WaitObservationDecision(decision="normal_waiting", reason="继续正常等待。", next_wait_ms=2),
        WaitObservationDecision(decision="normal_waiting", reason="继续正常等待。", next_wait_ms=2),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(
                normal_timeout_ms=3,
                abnormal_timeout_ms=10,
                min_wait_ms=1,
                max_wait_ms=10,
                default_wait_ms=1,
            ),
        )

    result = asyncio.run(_run())

    assert result.status == "normal_timeout"
    assert result.elapsed_ms == 3
    assert result.timeout_ms == 3
    assert result.terminal_decision == "normal_waiting"
    assert result.traces[-1].next_wait_ms == 0
    assert page.wait_calls == [2, 1]


def test_observe_until_ready_returns_abnormal_stuck_after_short_budget() -> None:
    page = FakePage()
    states = [
        make_page_state(text="状态 A"),
        make_page_state(text="状态 B"),
        make_page_state(text="状态 C"),
    ]
    decisions = [
        WaitObservationDecision(decision="abnormal_stuck", reason="页面无响应。", next_wait_ms=2),
        WaitObservationDecision(decision="abnormal_stuck", reason="页面仍无响应。", next_wait_ms=2),
        WaitObservationDecision(decision="abnormal_stuck", reason="页面异常卡住。", next_wait_ms=2),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(
                normal_timeout_ms=100,
                abnormal_timeout_ms=3,
                min_wait_ms=1,
                max_wait_ms=10,
                default_wait_ms=1,
            ),
        )

    result = asyncio.run(_run())

    assert result.status == "abnormal_stuck"
    assert result.elapsed_ms == 3
    assert result.timeout_ms == 3
    assert result.terminal_decision == "abnormal_stuck"
    assert result.traces[-1].next_wait_ms == 0
    assert page.wait_calls == [2, 1]


def test_observe_until_ready_keeps_abnormal_budget_after_normal_waiting() -> None:
    page = FakePage()
    states = [
        make_page_state(text="状态 A"),
        make_page_state(text="状态 B"),
        make_page_state(text="状态 C"),
        make_page_state(text="状态 D"),
    ]
    decisions = [
        WaitObservationDecision(decision="abnormal_stuck", reason="页面无响应。", next_wait_ms=2),
        WaitObservationDecision(decision="normal_waiting", reason="短暂出现正常等待提示。", next_wait_ms=1),
        WaitObservationDecision(decision="abnormal_stuck", reason="再次异常卡住。", next_wait_ms=2),
        WaitObservationDecision(decision="abnormal_stuck", reason="异常卡住预算耗尽。", next_wait_ms=2),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(
                normal_timeout_ms=100,
                abnormal_timeout_ms=3,
                min_wait_ms=1,
                max_wait_ms=10,
                default_wait_ms=1,
            ),
        )

    result = asyncio.run(_run())

    assert result.status == "abnormal_stuck"
    assert result.elapsed_ms == 4
    assert page.wait_calls == [2, 1, 1]


def test_observe_until_ready_clamps_invalid_wait_ms() -> None:
    page = FakePage()
    states = [make_page_state(text="状态 A"), make_page_state(text="状态 B")]
    decisions = [
        WaitObservationDecision(decision="normal_waiting", reason="继续等待。", next_wait_ms=0),
        WaitObservationDecision(decision="task_completed", reason="完成。", next_wait_ms=0),
    ]

    async def _run():
        observe_fn = await observe_sequence(states)
        classify_fn = await decision_sequence(decisions)
        return await observe_until_ready(
            page,
            observe_fn=observe_fn,
            classify_fn=classify_fn,
            options=WaitObservationOptions(
                normal_timeout_ms=10,
                abnormal_timeout_ms=10,
                min_wait_ms=1,
                max_wait_ms=5,
                default_wait_ms=3,
            ),
        )

    result = asyncio.run(_run())

    assert result.status == "success"
    assert page.wait_calls == [3]
    assert result.traces[0].next_wait_ms == 3

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.execution.observer import observe_page
from backend.schemas.run_schemas import ObservedPageState

WaitObservationStatus = Literal["success", "actionable", "timeout"]
WaitObservationDecisionName = Literal["continue_waiting", "ready_for_next_action", "task_completed"]


class WaitObservationDecision(BaseModel):
    decision: WaitObservationDecisionName
    reason: str = Field(description="一句中文说明判断依据。")


@dataclass(frozen=True)
class WaitObservationOptions:
    interval_ms: int = 2000
    timeout_ms: int = 600_000


@dataclass(frozen=True)
class WaitObservationTrace:
    observation_index: int
    elapsed_ms: int
    decision: WaitObservationDecisionName
    reason: str


@dataclass(frozen=True)
class WaitObservationResult:
    status: WaitObservationStatus
    page_state: ObservedPageState
    observations: int
    reason: str
    traces: list[WaitObservationTrace] = field(default_factory=list)


DecisionFn = Callable[[ObservedPageState, int, int], Awaitable[WaitObservationDecision]]


async def observe_until_ready(
    page: Any,
    *,
    classify_fn: DecisionFn,
    observe_fn: Callable[[Any], Awaitable[ObservedPageState]] = observe_page,
    options: WaitObservationOptions = WaitObservationOptions(),
) -> WaitObservationResult:
    elapsed_ms = 0
    observations = 0
    latest_page_state: ObservedPageState | None = None
    traces: list[WaitObservationTrace] = []

    while elapsed_ms <= options.timeout_ms:
        page_state = await observe_fn(page)
        latest_page_state = page_state
        observations += 1

        decision = await classify_fn(page_state, elapsed_ms, observations)
        traces.append(
            WaitObservationTrace(
                observation_index=observations,
                elapsed_ms=elapsed_ms,
                decision=decision.decision,
                reason=decision.reason,
            )
        )
        if decision.decision == "task_completed":
            return WaitObservationResult("success", page_state, observations, decision.reason, traces)
        if decision.decision == "ready_for_next_action":
            return WaitObservationResult("actionable", page_state, observations, decision.reason, traces)

        if elapsed_ms >= options.timeout_ms:
            break

        await page.wait_for_timeout(options.interval_ms)
        elapsed_ms += options.interval_ms

    if latest_page_state is None:
        latest_page_state = await observe_fn(page)
        observations += 1

    return WaitObservationResult(
        "timeout",
        latest_page_state,
        observations,
        "等待超过 10 分钟，仍未出现可继续操作或完成状态。",
        traces,
    )

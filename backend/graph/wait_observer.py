# 技术栈：Python 3.10 + Pydantic + Playwright
# 作用：把页面观察、模型判断和受控等待收敛成一条可追踪的等待链路。

from __future__ import annotations

import time

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from backend.execution.observer import observe_page
from backend.schemas.run_schemas import ObservedPageState, WaitObservationDecisionName, WaitObservationStatus


class WaitObservationDecision(BaseModel):
    decision: WaitObservationDecisionName
    reason: str = Field(description="一句中文说明判断依据。")
    next_wait_ms: int = Field(default=2000, description="下一次观察前建议等待的毫秒数。")


@dataclass(frozen=True)
class WaitObservationOptions:
    normal_timeout_ms: int = 600_000
    abnormal_timeout_ms: int = 30_000
    min_wait_ms: int = 500
    max_wait_ms: int = 30_000
    default_wait_ms: int = 2_000


@dataclass(frozen=True)
class WaitObservationTrace:
    observation_index: int
    elapsed_ms: int
    normal_wait_elapsed_ms: int
    abnormal_wait_elapsed_ms: int
    decision: WaitObservationDecisionName
    reason: str
    next_wait_ms: int
    screenshot_path: str | None = None


@dataclass(frozen=True)
class WaitObservationResult:
    status: WaitObservationStatus
    page_state: ObservedPageState
    observations: int
    reason: str
    elapsed_ms: int
    timeout_ms: int
    terminal_decision: WaitObservationDecisionName | None = None
    traces: list[WaitObservationTrace] = field(default_factory=list)


DecisionFn = Callable[[ObservedPageState, int, int, int, int], Awaitable[WaitObservationDecision]]
CaptureTraceScreenshotFn = Callable[[int], Awaitable[str | None]]


# 根据模型给出的等待时长、剩余预算和配置参数，裁剪出单次可执行的等待时间。
def _clamp_wait_ms(raw_wait_ms: int, remaining_ms: int, options: WaitObservationOptions) -> int:
    wait_ms = raw_wait_ms if raw_wait_ms > 0 else options.default_wait_ms
    wait_ms = max(options.min_wait_ms, min(wait_ms, options.max_wait_ms))
    return min(wait_ms, remaining_ms)


# 持续观察页面并按模型决策等待、结束或返回可操作状态，同时记录每轮轨迹。
async def observe_until_ready(
    page: Any,
    *,
    classify_fn: DecisionFn,
    observe_fn: Callable[[Any], Awaitable[ObservedPageState]] = observe_page,
    capture_trace_screenshot_fn: CaptureTraceScreenshotFn | None = None,
    options: WaitObservationOptions = WaitObservationOptions(),
) -> WaitObservationResult:
    elapsed_ms = 0
    normal_wait_elapsed_ms = 0
    abnormal_wait_elapsed_ms = 0
    observations = 0
    traces: list[WaitObservationTrace] = []

    while True:
        loop_started_at = time.monotonic()
        page_state = await observe_fn(page)
        observations += 1
        normal_remaining_ms = max(0, options.normal_timeout_ms - normal_wait_elapsed_ms)
        abnormal_remaining_ms = max(0, options.abnormal_timeout_ms - abnormal_wait_elapsed_ms)
        decision = await classify_fn(
            page_state,
            elapsed_ms,
            observations,
            normal_remaining_ms,
            abnormal_remaining_ms,
        )
        screenshot_path = (
            await capture_trace_screenshot_fn(observations)
            if capture_trace_screenshot_fn is not None
            else None
        )
        processing_ms = max(0, int((time.monotonic() - loop_started_at) * 1000))
        elapsed_ms += processing_ms
        if decision.decision in {"normal_waiting", "abnormal_stuck"}:
            if decision.decision == "normal_waiting":
                normal_wait_elapsed_ms += processing_ms
            else:
                abnormal_wait_elapsed_ms += processing_ms

        if decision.decision == "task_completed":
            traces.append(
                WaitObservationTrace(
                    observations,
                    elapsed_ms,
                    normal_wait_elapsed_ms,
                    abnormal_wait_elapsed_ms,
                    decision.decision,
                    decision.reason,
                    0,
                    screenshot_path,
                )
            )
            return WaitObservationResult(
                "success",
                page_state,
                observations,
                decision.reason,
                elapsed_ms,
                options.normal_timeout_ms,
                decision.decision,
                traces,
            )

        if decision.decision == "ready_for_next_action":
            traces.append(
                WaitObservationTrace(
                    observations,
                    elapsed_ms,
                    normal_wait_elapsed_ms,
                    abnormal_wait_elapsed_ms,
                    decision.decision,
                    decision.reason,
                    0,
                    screenshot_path,
                )
            )
            return WaitObservationResult(
                "actionable",
                page_state,
                observations,
                decision.reason,
                elapsed_ms,
                options.normal_timeout_ms,
                decision.decision,
                traces,
            )

        if decision.decision == "normal_waiting":
            remaining_ms = options.normal_timeout_ms - normal_wait_elapsed_ms
            if remaining_ms <= 0:
                traces.append(
                    WaitObservationTrace(
                        observations,
                        elapsed_ms,
                        normal_wait_elapsed_ms,
                        abnormal_wait_elapsed_ms,
                        decision.decision,
                        decision.reason,
                        0,
                        screenshot_path,
                    )
                )
                return WaitObservationResult(
                    "normal_timeout",
                    page_state,
                    observations,
                    "页面保持正常等待状态超过 10 分钟，仍未进入下一步或完成状态。",
                    elapsed_ms,
                    options.normal_timeout_ms,
                    decision.decision,
                    traces,
                )
            wait_ms = _clamp_wait_ms(decision.next_wait_ms, remaining_ms, options)
            traces.append(
                WaitObservationTrace(
                    observations,
                    elapsed_ms,
                    normal_wait_elapsed_ms,
                    abnormal_wait_elapsed_ms,
                    decision.decision,
                    decision.reason,
                    wait_ms,
                    screenshot_path,
                )
            )
            await page.wait_for_timeout(wait_ms)
            elapsed_ms += wait_ms
            normal_wait_elapsed_ms += wait_ms
            continue

        remaining_ms = options.abnormal_timeout_ms - abnormal_wait_elapsed_ms
        if remaining_ms <= 0:
            traces.append(
                WaitObservationTrace(
                    observations,
                    elapsed_ms,
                    normal_wait_elapsed_ms,
                    abnormal_wait_elapsed_ms,
                    decision.decision,
                    decision.reason,
                    0,
                    screenshot_path,
                )
            )
            return WaitObservationResult(
                "abnormal_stuck",
                page_state,
                observations,
                "页面疑似异常卡住，连续 30 秒没有恢复为正常等待、可操作或完成状态。",
                elapsed_ms,
                options.abnormal_timeout_ms,
                decision.decision,
                traces,
            )
        wait_ms = _clamp_wait_ms(decision.next_wait_ms, remaining_ms, options)
        traces.append(
            WaitObservationTrace(
                observations,
                elapsed_ms,
                normal_wait_elapsed_ms,
                abnormal_wait_elapsed_ms,
                decision.decision,
                decision.reason,
                wait_ms,
                screenshot_path,
            )
        )
        await page.wait_for_timeout(wait_ms)
        elapsed_ms += wait_ms
        abnormal_wait_elapsed_ms += wait_ms

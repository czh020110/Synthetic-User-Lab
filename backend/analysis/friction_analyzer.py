from __future__ import annotations

# ============================ 摩擦分析模块 ============================ #
# 模块功能: 基于步骤日志检测运行后摩擦模式，生成结构化摩擦问题
# 模块数据流: StepLog[] -> analyze_friction() -> FrictionIssue[]
# 模块接口说明: analyze_friction(steps) 返回结构化摩擦问题列表

from backend.schemas.run_schemas import FrictionIssue, FrictionSeverity, StepLog


def analyze_friction(steps: list[StepLog]) -> list[FrictionIssue]:
    """对步骤日志执行基础摩擦分析，返回结构化摩擦问题列表。"""

    if not steps:
        return []

    issues: list[FrictionIssue] = []
    issues.extend(_detect_repeated_clicks(steps))
    issues.extend(_detect_back_navigation(steps))
    issues.extend(_detect_error_recovery(steps))
    issues.extend(_detect_page_dwell(steps))
    issues.extend(_detect_lost_navigation(steps))
    issues.extend(_detect_misclick(steps))
    return issues


# ============================ 重复点击 ============================ #


def _detect_repeated_clicks(steps: list[StepLog]) -> list[FrictionIssue]:
    """检测同一元素连续点击多次且页面无响应的摩擦。"""

    issues: list[FrictionIssue] = []
    i = 0
    while i < len(steps):
        step = steps[i]
        if step.decided_action.action != "click":
            i += 1
            continue

        payload = step.decided_action.payload
        selector = getattr(payload, "selector", None)
        if not selector:
            i += 1
            continue

        group_indexes = [step.step_index]
        j = i + 1
        while j < len(steps):
            next_step = steps[j]
            if next_step.decided_action.action != "click":
                break
            next_selector = getattr(next_step.decided_action.payload, "selector", None)
            if next_selector != selector:
                break
            group_indexes.append(next_step.step_index)
            j += 1

        if len(group_indexes) >= 3:
            severity: FrictionSeverity = "high" if len(group_indexes) >= 5 else "medium"
            issues.append(FrictionIssue(
                signal="repeated_click",
                severity=severity,
                step_indexes=group_indexes,
                description=f"第 {group_indexes[0]}-{group_indexes[-1]} 步连续点击同一元素 {selector} {len(group_indexes)} 次，页面无响应。",
                suggested_fix="检查该元素是否正确响应点击事件，或增加点击后的状态反馈。",
            ))

        i = j

    return issues


# ============================ 返回导航 ============================ #


def _detect_back_navigation(steps: list[StepLog]) -> list[FrictionIssue]:
    """检测导航回已访问过的更早 URL 的返回行为。"""

    back_steps: list[int] = []
    seen_urls: list[str] = []

    for step in steps:
        current_url = step.observed_page_state.current_url
        if current_url not in seen_urls:
            seen_urls.append(current_url)

        if step.decided_action.action == "navigate":
            nav_url = getattr(step.decided_action.payload, "url", None)
            if nav_url and nav_url in seen_urls:
                back_steps.append(step.step_index)
                # navigate 动作的目标 URL 已在 seen_urls 中，不重复追加

        post_url = step.post_action_page_state.current_url
        if post_url not in seen_urls:
            seen_urls.append(post_url)

    if not back_steps:
        return []

    severity: FrictionSeverity = "medium" if len(back_steps) >= 2 else "low"
    return [FrictionIssue(
        signal="back_navigation",
        severity=severity,
        step_indexes=back_steps,
        description=f"第 {', '.join(str(i) for i in back_steps)} 步导航回已访问过的页面，表示用户可能走错路径。",
        suggested_fix="在关键分支点增加路径提示，减少用户需要返回的情况。",
    )]


# ============================ 错误恢复 ============================ #


def _detect_error_recovery(steps: list[StepLog]) -> list[FrictionIssue]:
    """检测动作执行失败、页面报错或触发恢复路径的摩擦。"""

    error_signals = {"action_failed", "page_error", "recovery_candidate"}
    error_steps: list[int] = []

    for step in steps:
        if error_signals & set(step.validation_result.friction_signals):
            error_steps.append(step.step_index)

    if not error_steps:
        return []

    return [FrictionIssue(
        signal="error_recovery",
        severity="high",
        step_indexes=error_steps,
        description=f"第 {', '.join(str(i) for i in error_steps)} 步出现执行失败或页面错误，触发了恢复路径。",
        suggested_fix="增加操作前的输入校验，减少执行失败的可能性。",
    )]


# ============================ 页面停留 ============================ #


def _detect_page_dwell(steps: list[StepLog]) -> list[FrictionIssue]:
    """检测同一 URL 连续多步无进展的页面停留摩擦。"""

    if not steps:
        return []

    issues: list[FrictionIssue] = []
    i = 0
    while i < len(steps):
        current_url = steps[i].observed_page_state.current_url
        group_indexes: list[int] = []

        j = i
        while j < len(steps):
            if steps[j].observed_page_state.current_url != current_url:
                break
            if steps[j].validation_result.detected_success:
                break
            # 只在步骤有停滞信号或页面内容无变化时计入停留组
            has_stall_signal = bool({"stuck_page", "repeated_wait", "repeated_action_target"} & set(steps[j].validation_result.friction_signals))
            page_unchanged = _normalize_text(steps[j].observed_page_state.visible_text_summary) == _normalize_text(steps[j].post_action_page_state.visible_text_summary)
            if has_stall_signal or page_unchanged:
                group_indexes.append(steps[j].step_index)
            else:
                # 有进展的步骤中断停留组
                break
            j += 1

        if len(group_indexes) >= 3:
            severity: FrictionSeverity = "high" if len(group_indexes) >= 5 else "medium"
            issues.append(FrictionIssue(
                signal="page_dwell",
                severity=severity,
                step_indexes=group_indexes,
                description=f"第 {group_indexes[0]}-{group_indexes[-1]} 步停留在同一页面 {current_url}，可能表示用户不确定下一步操作。",
                suggested_fix="在页面停留较久时增加操作引导或进度指示。",
            ))

        if j == i:
            i += 1
        else:
            i = j

    return issues


# ============================ 迷失导航 ============================ #


def _detect_lost_navigation(steps: list[StepLog]) -> list[FrictionIssue]:
    """检测连续偏离任务主路径的迷失导航摩擦。"""

    lost_steps: list[int] = []
    for step in steps:
        if "off_track_navigation" in step.validation_result.friction_signals:
            lost_steps.append(step.step_index)

    if not lost_steps:
        return []

    severity: FrictionSeverity = "high" if len(lost_steps) >= 5 else "medium"
    return [FrictionIssue(
        signal="lost_navigation",
        severity=severity,
        step_indexes=lost_steps,
        description=f"第 {', '.join(str(i) for i in lost_steps)} 步连续偏离任务主路径，可能迷失方向。",
        suggested_fix="增加面包屑导航或任务步骤提示，帮助用户回到主路径。",
    )]


# ============================ 误点 ============================ #


def _detect_misclick(steps: list[StepLog]) -> list[FrictionIssue]:
    """检测点击后执行失败、页面报错或紧接着修正操作的误点摩擦。"""

    misclick_steps: list[int] = []

    for i, step in enumerate(steps):
        if step.decided_action.action != "click":
            continue

        # 情况 1：click 执行失败
        if not step.execution_result.success:
            misclick_steps.append(step.step_index)
            continue

        # 情况 2：click 后页面出现错误
        if step.post_action_page_state.error_messages:
            misclick_steps.append(step.step_index)
            continue

        # 情况 3：click 后紧接着不同 click，且页面无可见变化
        if i + 1 < len(steps):
            next_step = steps[i + 1]
            if next_step.decided_action.action == "click":
                current_selector = getattr(step.decided_action.payload, "selector", "")
                next_selector = getattr(next_step.decided_action.payload, "selector", "")
                if current_selector and next_selector and current_selector != next_selector:
                    before_text = step.observed_page_state.visible_text_summary
                    after_text = step.post_action_page_state.visible_text_summary
                    if _normalize_text(before_text) == _normalize_text(after_text):
                        misclick_steps.append(step.step_index)

    if not misclick_steps:
        return []

    return [FrictionIssue(
        signal="misclick",
        severity="low",
        step_indexes=misclick_steps,
        description=f"第 {', '.join(str(i) for i in misclick_steps)} 步点击后页面无变化或出现错误，可能为误点。",
        suggested_fix="对不可逆操作增加确认提示，减少误操作影响。",
    )]


def _normalize_text(text: str) -> str:
    """规范化文本用于比较：去除多余空白。"""

    return " ".join(text.split())

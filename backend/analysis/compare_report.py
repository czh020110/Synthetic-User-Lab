from __future__ import annotations

# ============================ 跨 persona 对比报告模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 对同一 task 的多个已完成 run 聚合跨 persona 对比报告
# 模块数据流: run_ids + RunStore -> 校验 -> 取 record/report -> 聚合 -> CompareReport
# 模块接口说明: build_compare_report() 纯代码聚合,不依赖 LLM,供 API 与 acceptance 复用

from backend.schemas.run_schemas import CompareItem, CompareReport, RunRecord, RunReport
from backend.stores.run_store_protocol import RunStore


class CompareError(Exception):
    """对比报告聚合基础错误，API 层据子类转对应 HTTP 状态码。"""


class RunNotFoundError(CompareError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Run not found: {run_id}")
        self.run_id = run_id


class RunNotReadyError(CompareError):
    def __init__(self, run_id: str, status: str) -> None:
        super().__init__(f"Run {run_id} is not finished (status={status})")
        self.run_id = run_id
        self.status = status


class TaskMismatchError(CompareError):
    def __init__(self, run_id: str, expected_task_id: str, actual_task_id: str) -> None:
        super().__init__(
            f"Run {run_id} belongs to task {actual_task_id}, expected {expected_task_id}"
        )
        self.run_id = run_id
        self.expected_task_id = expected_task_id
        self.actual_task_id = actual_task_id


_TERMINAL_STATUSES = {"succeeded", "failed"}


def build_compare_report(run_ids: list[str], store: RunStore) -> CompareReport:
    """对一组同 task 的已完成 run 聚合跨 persona 对比报告。

    校验失败抛 CompareError 子类；成功返回纯代码聚合结果，不调用 LLM。
    """

    items: list[CompareItem] = []
    task = None
    for run_id in run_ids:
        record = store.get_record(run_id)
        if record is None:
            raise RunNotFoundError(run_id)
        if record.status not in _TERMINAL_STATUSES:
            raise RunNotReadyError(run_id, record.status)
        if task is None:
            task = record.task
        elif record.task.id != task.id:
            raise TaskMismatchError(run_id, task.id, record.task.id)
        report = store.get_report(run_id)
        items.append(_build_compare_item(run_id, record, report))

    # run_ids 非空且至少一个 record 存在时 task 必定被赋值，此处仅为类型收窄
    assert task is not None

    success_count = sum(1 for item in items if item.success)
    conclusion_distribution = {"keep": 0, "optimize": 0, "fix": 0}
    for item in items:
        conclusion_distribution[item.conclusion] += 1
    avg_steps = sum(item.total_steps for item in items) / len(items)
    total_friction_signals = sum(item.friction_signal_count for item in items)

    return CompareReport(
        task=task,
        run_count=len(items),
        success_count=success_count,
        conclusion_distribution=conclusion_distribution,
        avg_steps=round(avg_steps, 2),
        total_friction_signals=total_friction_signals,
        items=items,
        comparison_summary=_build_comparison_summary(
            items, success_count, conclusion_distribution, avg_steps, total_friction_signals
        ),
    )


def _build_compare_item(run_id: str, record: RunRecord, report: RunReport | None) -> CompareItem:
    """从 record/report 构造对比条目。

    fail_run 路径下 run 可能没有 report，此时从 record 构造失败条目。
    """

    if report is not None:
        return CompareItem(
            run_id=run_id,
            persona=report.persona,
            success=report.success,
            conclusion=report.conclusion,
            total_steps=report.total_steps,
            friction_signal_count=len(report.friction_signals),
            friction_issue_count=len(report.friction_issues),
            friction_signals=report.friction_signals,
            friction_issues=report.friction_issues,
            summary=report.summary,
            key_findings=report.key_findings,
        )

    return CompareItem(
        run_id=run_id,
        persona=record.persona,
        success=False,
        conclusion="fix",
        total_steps=0,
        friction_signal_count=0,
        friction_issue_count=0,
        friction_signals=[],
        friction_issues=[],
        summary=record.error_message or "run 失败且未生成报告",
        key_findings=[],
    )


def _build_comparison_summary(
    items: list[CompareItem],
    success_count: int,
    distribution: dict[str, int],
    avg_steps: float,
    total_friction: int,
) -> str:
    """生成纯代码的对比总结文案。"""

    parts = [f"共 {len(items)} 个 persona 完成同一任务"]
    parts.append(f"{success_count} 个成功、{len(items) - success_count} 个失败")
    dist_parts = [f"{conclusion}={count}" for conclusion, count in distribution.items() if count > 0]
    if dist_parts:
        parts.append("结论分布 " + "/".join(dist_parts))
    parts.append(f"平均 {avg_steps:.1f} 步")
    parts.append(f"累计 {total_friction} 条摩擦信号")
    return "；".join(parts) + "。"

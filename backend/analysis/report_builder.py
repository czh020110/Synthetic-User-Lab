from __future__ import annotations

# ============================ 报告生成模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 基于步骤日志整理最终 run 报告
# 模块数据流: RunRecord + StepLog[] -> RunReport
# 模块接口说明: build_run_report() 返回最终结构化报告

from backend.schemas.run_schemas import RunRecord, RunReport, StepLog


def build_run_report(record: RunRecord, steps: list[StepLog]) -> RunReport:
    """生成当前 run 的简版报告。"""

    success = bool(steps and steps[-1].validation_result.detected_success)
    friction_signals: list[str] = []
    for step in steps:
        friction_signals.extend(step.validation_result.friction_signals)

    key_findings = [
        f"共执行 {len(steps)} 步。",
        f"最终状态为 {'成功' if success else '失败'}。",
    ]
    if friction_signals:
        key_findings.append(f"检测到摩擦信号: {', '.join(sorted(set(friction_signals)))}。")

    recommendations = [
        "继续扩展 persona、task 与失败恢复分支。",
        "将内存存储替换为数据库持久化。",
    ]
    if not success:
        recommendations.insert(0, "优先检查 Demo 页面流程或执行动作映射是否与页面状态一致。")

    return RunReport(
        run_id=record.run_id,
        status="succeeded" if success else "failed",
        summary="任务执行成功。" if success else "任务未完成。",
        success=success,
        persona=record.persona,
        task=record.task,
        total_steps=len(steps),
        friction_signals=sorted(set(friction_signals)),
        key_findings=key_findings,
        next_recommendations=recommendations,
    )

from __future__ import annotations

# ============================ 报告渲染模块 ============================ #
# 使用技术栈: Python
# 模块功能: 将 RunReport 渲染为人类可读的 Markdown 文本
# 模块接口说明: render_report_markdown(report) -> str


from backend.schemas.run_schemas import RunReport


def render_report_markdown(report: RunReport) -> str:
    """将 RunReport 渲染为人类可读的 Markdown 文本。"""

    sections: list[str] = []

    # 基本信息
    sections.append("# Synthetic User Lab Run Report\n")
    sections.append("## 基本信息\n")
    sections.append(f"- **Run ID**: {report.run_id}")
    sections.append(f"- **状态**: {report.status}")
    sections.append(f"- **结论**: {report.conclusion}")
    sections.append(f"- **总步数**: {report.total_steps}")
    sections.append("")

    # Persona
    sections.append("## Persona\n")
    sections.append(f"- **名称**: {report.persona.name}")
    sections.append(f"- **熟练度**: {report.persona.skill_level}")
    sections.append(f"- **耐心**: {report.persona.patience_level}")
    sections.append(f"- **风险偏好**: {report.persona.risk_preference}")
    if report.persona.description:
        sections.append(f"- **描述**: {report.persona.description}")
    sections.append("")

    # 任务
    sections.append("## 任务\n")
    sections.append(f"- **名称**: {report.task.name}")
    sections.append(f"- **起始 URL**: {report.task.start_url}")
    if report.task.success_criteria:
        sections.append("- **成功条件**:")
        for criterion in report.task.success_criteria:
            sections.append(f"  - {criterion}")
    sections.append("")

    # 执行摘要
    sections.append("## 执行摘要\n")
    sections.append(report.summary)
    sections.append("")

    # 关键发现
    if report.key_findings:
        sections.append("## 关键发现\n")
        for finding in report.key_findings:
            sections.append(f"- {finding}")
        sections.append("")

    # 关键截图
    if report.key_screenshots:
        sections.append("## 关键截图\n")
        for ks in report.key_screenshots:
            sections.append(f"- **{ks.label}**（步骤 {ks.step_index}，{ks.source}）：`{ks.path}`")
        sections.append("")

    # 摩擦问题
    if report.friction_issues:
        sections.append("## 摩擦问题\n")
        for issue in report.friction_issues:
            sections.append(f"- **{issue.signal}**（{issue.severity}）：{issue.description}")
            if issue.suggested_fix:
                sections.append(f"  → 建议：{issue.suggested_fix}")
        sections.append("")

    # 后续建议
    if report.next_recommendations:
        sections.append("## 后续建议\n")
        for rec in report.next_recommendations:
            sections.append(f"- {rec}")
        sections.append("")

    # 步骤明细
    if report.step_details:
        sections.append("## 步骤明细\n")
        sections.append("| 步骤 | 动作 | 执行 | 验证 | 摩擦信号 |")
        sections.append("|------|------|------|------|----------|")
        for step in report.step_details:
            idx = step.get("step_index", "?")
            action = step.get("action", "?")
            exec_ok = "✓" if step.get("execution_success") else "✗"
            val_status = step.get("validation_status", "?")
            friction = ", ".join(step.get("validation_friction_signals", [])) or "-"
            sections.append(f"| {idx} | {action} | {exec_ok} | {val_status} | {friction} |")
        sections.append("")

    # 错误信息
    if report.error_message:
        sections.append("## 错误信息\n")
        sections.append(f"- **类型**: {report.error_type or '未知'}")
        sections.append(f"- **消息**: {report.error_message}")
        sections.append("")

    return "\n".join(sections)

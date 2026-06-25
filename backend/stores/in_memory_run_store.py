from __future__ import annotations

# ============================ 内存运行存储模块 ============================ #
# 使用技术栈: Python / Pydantic
# 模块功能: 保存 run 的状态、步骤日志与最终报告
# 模块数据流: API 创建记录 -> 图执行逐步写入 -> API 查询状态/步骤/报告
# 模块接口说明: InMemoryRunStore 提供 create/get/update/complete/fail 方法

from backend.core.utils import utc_now
from backend.schemas.run_schemas import RunErrorType, RunRecord, RunReport, RunStatusResponse, StepLog


class InMemoryRunStore:
    """管理当前进程中的 run 数据。"""
    # 记录在内存的 run 记录

    def __init__(self) -> None:
        self._records: dict[str, RunRecord] = {}  # run 的主记录
        self._steps: dict[str, list[StepLog]] = {}  # run 的步骤列表
        self._reports: dict[str, RunReport] = {}  # run 的最终报告

    def clear(self) -> None:
        """清空全部内存数据。"""

        self._records.clear()
        self._steps.clear()
        self._reports.clear()

    def create_run(self, record: RunRecord) -> RunRecord:
        """创建新的运行记录。"""

        self._records[record.run_id] = record
        self._steps[record.run_id] = []
        return record.model_copy(deep=True)  # 返回深拷贝, 步直接改坏存储对象
        # 浅拷贝:只复制值, 深拷贝:值和地址都复制

    def mark_running(self, run_id: str) -> RunRecord:
        """更新记录为运行中状态。"""
        # 标记 run 正在运行中
        record = self._records[run_id]
        record.status = "running"  # 运行状态
        record.updated_at = utc_now()  # 更新为当前的时间
        return record.model_copy(deep=True)

    def add_step(self, run_id: str, step: StepLog) -> StepLog:
        """追加单步日志。"""

        self._steps[run_id].append(step)
        self._records[run_id].updated_at = utc_now()
        return step.model_copy(deep=True)

    def complete_run(self, run_id: str, report: RunReport) -> RunRecord:
        """写入报告并标记运行成功或失败结束。"""

        self._reports[run_id] = report  # 先保存报告
        record = self._records[run_id]
        record.status = report.status
        record.updated_at = utc_now()
        if report.status == "succeeded":
            record.error_type = None
            record.error_message = None  # 成功则清理错误信息
        return record.model_copy(deep=True)

    def fail_run(self, run_id: str, error_message: str, error_type: RunErrorType = "system_error") -> RunRecord:
        """记录异常并标记运行失败。"""

        record = self._records[run_id]
        record.status = "failed"  # 错误状态
        record.updated_at = utc_now()  # 更新时间
        record.error_type = error_type
        record.error_message = error_message  # 错误信息
        return record.model_copy(deep=True)

    def get_record(self, run_id: str) -> RunRecord | None:
        """返回运行记录。"""

        record = self._records.get(run_id)  # 读取某个 run 的主记录
        return record.model_copy(deep=True) if record else None

    def get_status(self, run_id: str) -> RunStatusResponse | None:
        """返回运行状态摘要。"""
        # 步返回完整步骤和报告

        record = self._records.get(run_id)
        if record is None:
            return None
        return RunStatusResponse(
            run_id=record.run_id,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            error_type=record.error_type,
            error_message=record.error_message,
        )

    def get_steps(self, run_id: str) -> list[StepLog] | None:
        """返回运行步骤列表。"""

        steps = self._steps.get(run_id)
        if steps is None:
            return None
        return [step.model_copy(deep=True) for step in steps]

    def get_report(self, run_id: str) -> RunReport | None:
        """返回最终报告。"""

        report = self._reports.get(run_id)
        return report.model_copy(deep=True) if report else None

    def list_run_ids(self) -> list[str]:
        """返回所有 run_id 列表，按创建时间倒序。"""

        records = sorted(self._records.values(), key=lambda r: r.created_at, reverse=True)
        return [r.run_id for r in records]

# model_copy复制模型对象pydantic, 用来:复制但需要修改,只复制的情况
# 用于返回一个完全独立的副本, 调用方法修改这个返回值不会直接影响保存的原始报告
run_store = InMemoryRunStore()  # 全局共享存储单例

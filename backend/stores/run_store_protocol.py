from __future__ import annotations

# ============================ RunStore 协议定义 ============================ #
# 使用技术栈: Python / typing.Protocol
# 模块功能: 定义运行存储层的统一接口，InMemoryRunStore 与 SqliteRunStore 均实现此协议
# 模块接口说明: RunStore Protocol 提供 create/get/update/complete/fail 方法签名

from typing import Protocol, runtime_checkable

from backend.schemas.run_schemas import RunErrorType, RunRecord, RunReport, RunStatusResponse, StepLog


@runtime_checkable
class RunStore(Protocol):
    """运行存储层统一接口。

    InMemoryRunStore 和 SqliteRunStore 均实现此协议。
    """

    def create_run(self, record: RunRecord) -> RunRecord:
        """创建新的运行记录。"""
        ...

    def mark_running(self, run_id: str) -> RunRecord:
        """更新记录为运行中状态。"""
        ...

    def add_step(self, run_id: str, step: StepLog) -> StepLog:
        """追加单步日志。"""
        ...

    def complete_run(self, run_id: str, report: RunReport) -> RunRecord:
        """写入报告并标记运行成功或失败结束。"""
        ...

    def fail_run(self, run_id: str, error_message: str, error_type: RunErrorType = "system_error") -> RunRecord:
        """记录异常并标记运行失败。"""
        ...

    def get_record(self, run_id: str) -> RunRecord | None:
        """返回运行记录。"""
        ...

    def get_status(self, run_id: str) -> RunStatusResponse | None:
        """返回运行状态摘要。"""
        ...

    def get_steps(self, run_id: str) -> list[StepLog] | None:
        """返回运行步骤列表。"""
        ...

    def get_report(self, run_id: str) -> RunReport | None:
        """返回最终报告。"""
        ...

    def list_run_ids(self) -> list[str]:
        """返回所有 run_id 列表，按创建时间倒序。"""
        ...

    def clear(self) -> None:
        """清空全部数据。仅用于测试。"""
        ...

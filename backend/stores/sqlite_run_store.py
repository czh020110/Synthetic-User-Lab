from __future__ import annotations

# ============================ SQLite 运行存储模块 ============================ #
# 使用技术栈: Python / sqlite3 / Pydantic
# 模块功能: 使用 SQLite 持久化保存 run 的状态、步骤日志与最终报告
# 模块数据流: API 创建记录 -> 图执行逐步写入 -> API 查询状态/步骤/报告
# 模块接口说明: SqliteRunStore 实现与 InMemoryRunStore 相同的接口
# 线程安全约束: 仅限事件循环单线程内同步调用，不支持多线程并发写同一连接

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from backend.schemas.run_schemas import (
    Persona,
    RunErrorType,
    RunRecord,
    RunReport,
    RunRequest,
    RunStatusResponse,
    StepLog,
    Task,
)


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS run_records (
    run_id        TEXT PRIMARY KEY,
    status        TEXT NOT NULL DEFAULT 'queued',
    request_json  TEXT NOT NULL,
    persona_json  TEXT NOT NULL,
    task_json     TEXT NOT NULL,
    error_type    TEXT,
    error_message TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS step_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL,
    step_index    INTEGER NOT NULL,
    step_json     TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES run_records(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS run_reports (
    run_id        TEXT PRIMARY KEY,
    report_json   TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES run_records(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_step_logs_run_id ON step_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_run_records_status ON run_records(status);
CREATE INDEX IF NOT EXISTS idx_run_records_created_at ON run_records(created_at);
"""


def utc_now() -> datetime:
    """返回当前 UTC 时间。"""

    return datetime.now(timezone.utc)


def _dt_to_str(dt: datetime) -> str:
    """将 datetime 序列化为 ISO 8601 UTC 字符串。"""

    return dt.isoformat()


def _str_to_dt(s: str) -> datetime:
    """将 ISO 8601 字符串反序列化为 datetime。"""

    return datetime.fromisoformat(s)


class SqliteRunStore:
    """使用 SQLite 持久化保存 run 数据。

    线程安全约束：仅限事件循环单线程内同步调用。
    单连接 + check_same_thread=False，无锁保护；
    若后续支持多 run 并发，需改为 thread-local 连接或加 threading.Lock。
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def initialize(self) -> None:
        """创建表和索引。启动时调用一次。"""

        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        conn.commit()

    def close(self) -> None:
        """关闭数据库连接。"""

        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def create_run(self, record: RunRecord) -> RunRecord:
        """创建新的运行记录。已存在时保留原始 created_at。"""

        conn = self._get_conn()
        now = _dt_to_str(utc_now())

        # 保留原始 created_at：若 run_id 已存在则不覆盖创建时间
        existing = conn.execute(
            "SELECT created_at FROM run_records WHERE run_id = ?",
            (record.run_id,),
        ).fetchone()
        created_at = existing["created_at"] if existing else _dt_to_str(record.created_at)

        # INSERT OR REPLACE 会通过 ON DELETE CASCADE 级联清空 step_logs 和 run_reports
        conn.execute(
            "INSERT OR REPLACE INTO run_records "
            "(run_id, status, request_json, persona_json, task_json, error_type, error_message, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.run_id,
                record.status,
                record.request.model_dump_json(),
                record.persona.model_dump_json(),
                record.task.model_dump_json(),
                record.error_type,
                record.error_message,
                created_at,
                now,
            ),
        )
        conn.commit()
        return self.get_record(record.run_id)  # type: ignore[return-value]

    def mark_running(self, run_id: str) -> RunRecord:
        """更新记录为运行中状态。"""

        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        conn.execute(
            "UPDATE run_records SET status = 'running', updated_at = ? WHERE run_id = ?",
            (now, run_id),
        )
        conn.commit()
        return self.get_record(run_id)  # type: ignore[return-value]

    def add_step(self, run_id: str, step: StepLog) -> StepLog:
        """追加单步日志。"""

        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        conn.execute(
            "INSERT INTO step_logs (run_id, step_index, step_json, created_at) VALUES (?, ?, ?, ?)",
            (run_id, step.step_index, step.model_dump_json(), now),
        )
        conn.execute(
            "UPDATE run_records SET updated_at = ? WHERE run_id = ?",
            (now, run_id),
        )
        conn.commit()
        return step.model_copy(deep=True)

    def complete_run(self, run_id: str, report: RunReport) -> RunRecord:
        """写入报告并标记运行成功或失败结束。"""

        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        conn.execute(
            "INSERT OR REPLACE INTO run_reports (run_id, report_json, created_at) VALUES (?, ?, ?)",
            (run_id, report.model_dump_json(), now),
        )
        if report.status == "succeeded":
            conn.execute(
                "UPDATE run_records SET status = ?, error_type = NULL, error_message = NULL, updated_at = ? WHERE run_id = ?",
                (report.status, now, run_id),
            )
        else:
            conn.execute(
                "UPDATE run_records SET status = ?, updated_at = ? WHERE run_id = ?",
                (report.status, now, run_id),
            )
        conn.commit()
        return self.get_record(run_id)  # type: ignore[return-value]

    def fail_run(self, run_id: str, error_message: str, error_type: RunErrorType = "system_error") -> RunRecord:
        """记录异常并标记运行失败。"""

        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        conn.execute(
            "UPDATE run_records SET status = 'failed', error_type = ?, error_message = ?, updated_at = ? WHERE run_id = ?",
            (error_type, error_message, now, run_id),
        )
        conn.commit()
        return self.get_record(run_id)  # type: ignore[return-value]

    def get_record(self, run_id: str) -> RunRecord | None:
        """返回运行记录。"""

        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM run_records WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None

        return RunRecord(
            run_id=row["run_id"],
            status=row["status"],
            request=RunRequest.model_validate_json(row["request_json"]),
            persona=Persona.model_validate_json(row["persona_json"]),
            task=Task.model_validate_json(row["task_json"]),
            created_at=_str_to_dt(row["created_at"]),
            updated_at=_str_to_dt(row["updated_at"]),
            error_type=row["error_type"],
            error_message=row["error_message"],
        )

    def get_status(self, run_id: str) -> RunStatusResponse | None:
        """返回运行状态摘要。"""

        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM run_records WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None

        return RunStatusResponse(
            run_id=row["run_id"],
            status=row["status"],
            created_at=_str_to_dt(row["created_at"]),
            updated_at=_str_to_dt(row["updated_at"]),
            error_type=row["error_type"],
            error_message=row["error_message"],
        )

    def get_steps(self, run_id: str) -> list[StepLog] | None:
        """返回运行步骤列表。"""

        conn = self._get_conn()
        # 先检查 run 是否存在
        row = conn.execute(
            "SELECT 1 FROM run_records WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None

        rows = conn.execute(
            "SELECT step_json FROM step_logs WHERE run_id = ? ORDER BY step_index, id",
            (run_id,),
        ).fetchall()
        return [StepLog.model_validate_json(r["step_json"]) for r in rows]

    def get_report(self, run_id: str) -> RunReport | None:
        """返回最终报告。"""

        conn = self._get_conn()
        row = conn.execute(
            "SELECT report_json FROM run_reports WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return RunReport.model_validate_json(row["report_json"])

    def clear(self) -> None:
        """清空全部数据。仅用于测试。"""

        conn = self._get_conn()
        conn.execute("DELETE FROM run_reports")
        conn.execute("DELETE FROM step_logs")
        conn.execute("DELETE FROM run_records")
        conn.commit()

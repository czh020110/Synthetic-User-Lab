from __future__ import annotations

# ============================ PostgreSQL 运行存储模块 ============================ #
# 模块功能: 使用 PostgreSQL 持久化保存 run 的状态、步骤日志与最终报告
# 模块接口说明: PostgresRunStore 实现与 InMemoryRunStore / SqliteRunStore 相同的接口

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from backend.core.utils import utc_now
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

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS run_records (
        run_id        TEXT PRIMARY KEY,
        status        TEXT NOT NULL DEFAULT 'queued',
        request_json  JSONB NOT NULL,
        persona_json  JSONB NOT NULL,
        task_json     JSONB NOT NULL,
        error_type    TEXT,
        error_message TEXT,
        created_at    TIMESTAMPTZ NOT NULL,
        updated_at    TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS step_logs (
        id            BIGSERIAL PRIMARY KEY,
        run_id        TEXT NOT NULL REFERENCES run_records(run_id) ON DELETE CASCADE,
        step_index    INTEGER NOT NULL,
        step_json     JSONB NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS run_reports (
        run_id        TEXT PRIMARY KEY REFERENCES run_records(run_id) ON DELETE CASCADE,
        report_json   JSONB NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_step_logs_run_id ON step_logs(run_id)",
    "CREATE INDEX IF NOT EXISTS idx_run_records_status ON run_records(status)",
    "CREATE INDEX IF NOT EXISTS idx_run_records_created_at ON run_records(created_at)",
)


def _jsonb_payload(model: Any) -> Jsonb:
    return Jsonb(model.model_dump(mode="json"))


def _model_from_payload(model_cls: Any, payload: Any) -> Any:
    if isinstance(payload, str):
        return model_cls.model_validate_json(payload)
    return model_cls.model_validate(payload)


class PostgresRunStore:
    """使用 PostgreSQL 持久化保存 run 数据。"""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: ConnectionPool | None = None

    def _get_pool(self) -> ConnectionPool:
        if self._pool is None:
            pool = ConnectionPool(
                conninfo=self._database_url,
                min_size=1,
                max_size=4,
                kwargs={"row_factory": dict_row},
                open=True,
            )
            try:
                pool.wait()
            except Exception:
                pool.close()
                raise
            self._pool = pool
        return self._pool

    def initialize(self) -> None:
        """创建表和索引。启动时调用一次。"""

        with self._get_pool().connection() as conn:
            with conn.transaction():
                for statement in SCHEMA_STATEMENTS:
                    conn.execute(statement)

    def close(self) -> None:
        """关闭连接池。"""

        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def create_run(self, record: RunRecord) -> RunRecord:
        """创建新的运行记录。已存在时保留原始 created_at。"""

        now = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                existing = conn.execute(
                    "SELECT created_at FROM run_records WHERE run_id = %s",
                    (record.run_id,),
                ).fetchone()
                created_at = existing["created_at"] if existing is not None else record.created_at
                conn.execute("DELETE FROM run_reports WHERE run_id = %s", (record.run_id,))
                conn.execute("DELETE FROM step_logs WHERE run_id = %s", (record.run_id,))
                conn.execute(
                    """
                    INSERT INTO run_records (
                        run_id, status, request_json, persona_json, task_json,
                        error_type, error_message, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        request_json = EXCLUDED.request_json,
                        persona_json = EXCLUDED.persona_json,
                        task_json = EXCLUDED.task_json,
                        error_type = EXCLUDED.error_type,
                        error_message = EXCLUDED.error_message,
                        created_at = run_records.created_at,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (
                        record.run_id,
                        record.status,
                        _jsonb_payload(record.request),
                        _jsonb_payload(record.persona),
                        _jsonb_payload(record.task),
                        record.error_type,
                        record.error_message,
                        created_at,
                        now,
                    ),
                )
        return self.get_record(record.run_id)  # type: ignore[return-value]

    def mark_running(self, run_id: str) -> RunRecord:
        """更新记录为运行中状态。"""

        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    "UPDATE run_records SET status = 'running', updated_at = %s WHERE run_id = %s",
                    (utc_now(), run_id),
                )
        return self.get_record(run_id)  # type: ignore[return-value]

    def add_step(self, run_id: str, step: StepLog) -> StepLog:
        """追加单步日志。"""

        now = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    "INSERT INTO step_logs (run_id, step_index, step_json, created_at) VALUES (%s, %s, %s, %s)",
                    (run_id, step.step_index, _jsonb_payload(step), now),
                )
                conn.execute(
                    "UPDATE run_records SET updated_at = %s WHERE run_id = %s",
                    (now, run_id),
                )
        return step.model_copy(deep=True)

    def complete_run(self, run_id: str, report: RunReport) -> RunRecord:
        """写入报告并标记运行成功或失败结束。"""

        now = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO run_reports (run_id, report_json, created_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET
                        report_json = EXCLUDED.report_json,
                        created_at = EXCLUDED.created_at
                    """,
                    (run_id, _jsonb_payload(report), now),
                )
                if report.status == "succeeded":
                    conn.execute(
                        "UPDATE run_records SET status = %s, error_type = NULL, error_message = NULL, updated_at = %s WHERE run_id = %s",
                        (report.status, now, run_id),
                    )
                else:
                    conn.execute(
                        "UPDATE run_records SET status = %s, updated_at = %s WHERE run_id = %s",
                        (report.status, now, run_id),
                    )
        return self.get_record(run_id)  # type: ignore[return-value]

    def fail_run(self, run_id: str, error_message: str, error_type: RunErrorType = "system_error") -> RunRecord:
        """记录异常并标记运行失败。"""

        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    "UPDATE run_records SET status = 'failed', error_type = %s, error_message = %s, updated_at = %s WHERE run_id = %s",
                    (error_type, error_message, utc_now(), run_id),
                )
        return self.get_record(run_id)  # type: ignore[return-value]

    def get_record(self, run_id: str) -> RunRecord | None:
        """返回运行记录。"""

        with self._get_pool().connection() as conn:
            row = conn.execute(
                "SELECT * FROM run_records WHERE run_id = %s",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return RunRecord(
            run_id=row["run_id"],
            status=row["status"],
            request=_model_from_payload(RunRequest, row["request_json"]),
            persona=_model_from_payload(Persona, row["persona_json"]),
            task=_model_from_payload(Task, row["task_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_type=row["error_type"],
            error_message=row["error_message"],
        )

    def get_status(self, run_id: str) -> RunStatusResponse | None:
        """返回运行状态摘要。"""

        with self._get_pool().connection() as conn:
            row = conn.execute(
                "SELECT * FROM run_records WHERE run_id = %s",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return RunStatusResponse(
            run_id=row["run_id"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_type=row["error_type"],
            error_message=row["error_message"],
        )

    def get_steps(self, run_id: str) -> list[StepLog] | None:
        """返回运行步骤列表。"""

        with self._get_pool().connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM run_records WHERE run_id = %s",
                (run_id,),
            ).fetchone()
            if exists is None:
                return None
            rows = conn.execute(
                "SELECT step_json FROM step_logs WHERE run_id = %s ORDER BY step_index, id",
                (run_id,),
            ).fetchall()
        return [_model_from_payload(StepLog, row["step_json"]) for row in rows]

    def get_report(self, run_id: str) -> RunReport | None:
        """返回最终报告。"""

        with self._get_pool().connection() as conn:
            row = conn.execute(
                "SELECT report_json FROM run_reports WHERE run_id = %s",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return _model_from_payload(RunReport, row["report_json"])

    def list_run_ids(self) -> list[str]:
        """返回所有 run_id 列表，按创建时间倒序。"""

        with self._get_pool().connection() as conn:
            rows = conn.execute("SELECT run_id FROM run_records ORDER BY created_at DESC").fetchall()
        return [row["run_id"] for row in rows]

    def clear(self) -> None:
        """清空全部数据。仅用于测试。"""

        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute("DELETE FROM run_reports")
                conn.execute("DELETE FROM step_logs")
                conn.execute("DELETE FROM run_records")

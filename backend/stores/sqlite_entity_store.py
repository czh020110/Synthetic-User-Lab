from __future__ import annotations

# ============================ SQLite 实体存储模块 ============================ #
# 模块功能: 使用 SQLite 持久化保存 Persona/Task/KnowledgeItem
# 模块接口说明: SqliteEntityStore 实现 EntityStore Protocol
# 线程安全约束: 仅限事件循环单线程内同步调用，不支持多线程并发写同一连接

import sqlite3
from datetime import datetime
from pathlib import Path

from backend.core.utils import utc_now
from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemUpdate
from backend.schemas.persona_schemas import Persona, PersonaUpdate
from backend.schemas.settings_schemas import FRONTEND_SETTINGS_KEY, FrontendSettings
from backend.schemas.task_schemas import Task, TaskUpdate


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS personas (
    persona_id   TEXT PRIMARY KEY,
    persona_json TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_personas_created_at ON personas(created_at);

CREATE TABLE IF NOT EXISTS tasks (
    task_id      TEXT PRIMARY KEY,
    task_json    TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

CREATE TABLE IF NOT EXISTS knowledge_items (
    item_id      TEXT PRIMARY KEY,
    source_type  TEXT NOT NULL,
    item_json    TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_source_type ON knowledge_items(source_type);

CREATE TABLE IF NOT EXISTS frontend_settings (
    settings_key   TEXT PRIMARY KEY,
    settings_json  TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
"""


def _dt_to_str(dt: datetime) -> str:
    return dt.isoformat()


def _str_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


class SqliteEntityStore:
    """使用 SQLite 持久化保存实体数据。

    线程安全约束：仅限事件循环单线程内同步调用。
    与 SqliteRunStore 可共用同一数据库文件。
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

    # ============================ Persona CRUD ============================ #

    def create_persona(self, persona: Persona) -> Persona:
        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        try:
            conn.execute(
                "INSERT INTO personas (persona_id, persona_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (persona.id, persona.model_dump_json(), _dt_to_str(persona.created_at), now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # 已存在则静默跳过，与 InMemoryEntityStore 行为一致
            pass
        return self.get_persona(persona.id)  # type: ignore[return-value]

    def get_persona(self, persona_id: str) -> Persona | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM personas WHERE persona_id = ?", (persona_id,)).fetchone()
        if row is None:
            return None
        return Persona(
            id=row["persona_id"],
            **Persona.model_validate_json(row["persona_json"]).model_dump(exclude={"id", "created_at", "updated_at"}),
            created_at=_str_to_dt(row["created_at"]),
            updated_at=_str_to_dt(row["updated_at"]),
        )

    def list_personas(self) -> list[Persona]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM personas ORDER BY created_at").fetchall()
        return [self.get_persona(r["persona_id"]) for r in rows]  # type: ignore[misc]

    def update_persona(self, persona_id: str, updates: PersonaUpdate) -> Persona | None:
        existing = self.get_persona(persona_id)
        if existing is None:
            return None
        update_data = updates.model_dump(exclude_none=True)
        updated = existing.model_copy(update=update_data)
        updated.updated_at = utc_now()
        conn = self._get_conn()
        now = _dt_to_str(updated.updated_at)
        conn.execute(
            "UPDATE personas SET persona_json = ?, updated_at = ? WHERE persona_id = ?",
            (updated.model_dump_json(), now, persona_id),
        )
        conn.commit()
        return updated

    def delete_persona(self, persona_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM personas WHERE persona_id = ?", (persona_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ============================ Task CRUD ============================ #

    def create_task(self, task: Task) -> Task:
        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        try:
            conn.execute(
                "INSERT INTO tasks (task_id, task_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (task.id, task.model_dump_json(), _dt_to_str(task.created_at), now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        return self.get_task(task.id)  # type: ignore[return-value]

    def get_task(self, task_id: str) -> Task | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return Task(
            id=row["task_id"],
            **Task.model_validate_json(row["task_json"]).model_dump(exclude={"id", "created_at", "updated_at"}),
            created_at=_str_to_dt(row["created_at"]),
            updated_at=_str_to_dt(row["updated_at"]),
        )

    def list_tasks(self) -> list[Task]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at").fetchall()
        return [self.get_task(r["task_id"]) for r in rows]  # type: ignore[misc]

    def update_task(self, task_id: str, updates: TaskUpdate) -> Task | None:
        existing = self.get_task(task_id)
        if existing is None:
            return None
        update_data = updates.model_dump(exclude_none=True)
        updated = existing.model_copy(update=update_data)
        updated.updated_at = utc_now()
        conn = self._get_conn()
        now = _dt_to_str(updated.updated_at)
        conn.execute(
            "UPDATE tasks SET task_json = ?, updated_at = ? WHERE task_id = ?",
            (updated.model_dump_json(), now, task_id),
        )
        conn.commit()
        return updated

    def delete_task(self, task_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ============================ KnowledgeItem CRUD ============================ #

    def create_knowledge_item(self, item: KnowledgeItem) -> KnowledgeItem:
        conn = self._get_conn()
        now = _dt_to_str(utc_now())
        try:
            conn.execute(
                "INSERT INTO knowledge_items (item_id, source_type, item_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (item.id, item.source_type, item.model_dump_json(), _dt_to_str(item.created_at), now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        return self.get_knowledge_item(item.id)  # type: ignore[return-value]

    def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM knowledge_items WHERE item_id = ?", (item_id,)).fetchone()
        if row is None:
            return None
        return KnowledgeItem(
            id=row["item_id"],
            **KnowledgeItem.model_validate_json(row["item_json"]).model_dump(exclude={"id", "created_at", "updated_at"}),
            created_at=_str_to_dt(row["created_at"]),
            updated_at=_str_to_dt(row["updated_at"]),
        )

    def list_knowledge_items(self, source_type: str | None = None) -> list[KnowledgeItem]:
        conn = self._get_conn()
        if source_type is not None:
            rows = conn.execute("SELECT * FROM knowledge_items WHERE source_type = ? ORDER BY created_at", (source_type,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM knowledge_items ORDER BY created_at").fetchall()
        return [self.get_knowledge_item(r["item_id"]) for r in rows]  # type: ignore[misc]

    def update_knowledge_item(self, item_id: str, updates: KnowledgeItemUpdate) -> KnowledgeItem | None:
        existing = self.get_knowledge_item(item_id)
        if existing is None:
            return None
        update_data = updates.model_dump(exclude_none=True)
        updated = existing.model_copy(update=update_data)
        updated.updated_at = utc_now()
        conn = self._get_conn()
        now = _dt_to_str(updated.updated_at)
        conn.execute(
            "UPDATE knowledge_items SET item_json = ?, updated_at = ? WHERE item_id = ?",
            (updated.model_dump_json(), now, item_id),
        )
        conn.commit()
        return updated

    def delete_knowledge_item(self, item_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM knowledge_items WHERE item_id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ============================ FrontendSettings ============================ #

    def get_frontend_settings(self) -> FrontendSettings:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM frontend_settings WHERE settings_key = ?",
            (FRONTEND_SETTINGS_KEY,),
        ).fetchone()
        if row is None:
            # 读路径不写：未保存时返回默认值，仅在显式 PUT 时持久化，
            # 避免 GET 产生副作用与并发冷启动竞争。
            return FrontendSettings(settings_key=FRONTEND_SETTINGS_KEY)
        return FrontendSettings(
            settings_key=row["settings_key"],
            **FrontendSettings.model_validate_json(row["settings_json"]).model_dump(
                exclude={"settings_key", "created_at", "updated_at"}
            ),
            created_at=_str_to_dt(row["created_at"]),
            updated_at=_str_to_dt(row["updated_at"]),
        )

    def upsert_frontend_settings(self, settings: FrontendSettings) -> FrontendSettings:
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO frontend_settings (settings_key, settings_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(settings_key) DO UPDATE SET
                settings_json = excluded.settings_json,
                updated_at = excluded.updated_at
            """,
            (
                settings.settings_key,
                settings.model_dump_json(),
                _dt_to_str(settings.created_at),
                _dt_to_str(settings.updated_at),
            ),
        )
        conn.commit()
        return self.get_frontend_settings()

    # ============================ 通用 ============================ #

    def clear(self) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM frontend_settings")
        conn.execute("DELETE FROM knowledge_items")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM personas")
        conn.commit()

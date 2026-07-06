from __future__ import annotations

# ============================ PostgreSQL 实体存储模块 ============================ #
# 模块功能: 使用 PostgreSQL 持久化保存 Persona、Task、KnowledgeItem
# 模块接口说明: PostgresEntityStore 实现 EntityStore Protocol

from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from backend.core.utils import utc_now
from backend.schemas.knowledge_schemas import KnowledgeItem, KnowledgeItemUpdate
from backend.schemas.persona_schemas import Persona, PersonaUpdate
from backend.schemas.task_schemas import Task, TaskUpdate

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS personas (
        persona_id   TEXT PRIMARY KEY,
        persona_json JSONB NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL,
        updated_at   TIMESTAMPTZ NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_personas_created_at ON personas(created_at)",
    """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id      TEXT PRIMARY KEY,
        task_json    JSONB NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL,
        updated_at   TIMESTAMPTZ NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
    """
    CREATE TABLE IF NOT EXISTS knowledge_items (
        item_id      TEXT PRIMARY KEY,
        source_type  TEXT NOT NULL,
        item_json    JSONB NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL,
        updated_at   TIMESTAMPTZ NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_knowledge_items_source_type ON knowledge_items(source_type)",
)


def _jsonb_payload(model: Any) -> Jsonb:
    return Jsonb(model.model_dump(mode="json"))


def _model_from_payload(model_cls: Any, payload: Any) -> Any:
    if isinstance(payload, str):
        return model_cls.model_validate_json(payload)
    return model_cls.model_validate(payload)


class PostgresEntityStore:
    """使用 PostgreSQL 持久化保存实体数据。"""

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

    def create_persona(self, persona: Persona) -> Persona:
        now = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO personas (persona_id, persona_json, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (persona_id) DO NOTHING
                    """,
                    (persona.id, _jsonb_payload(persona), persona.created_at, now),
                )
        return self.get_persona(persona.id)  # type: ignore[return-value]

    def get_persona(self, persona_id: str) -> Persona | None:
        with self._get_pool().connection() as conn:
            row = conn.execute("SELECT * FROM personas WHERE persona_id = %s", (persona_id,)).fetchone()
        if row is None:
            return None
        persona = _model_from_payload(Persona, row["persona_json"])
        return Persona(
            id=row["persona_id"],
            **persona.model_dump(exclude={"id", "created_at", "updated_at"}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_personas(self) -> list[Persona]:
        with self._get_pool().connection() as conn:
            rows = conn.execute("SELECT persona_id FROM personas ORDER BY created_at").fetchall()
        return [self.get_persona(row["persona_id"]) for row in rows]  # type: ignore[misc]

    def update_persona(self, persona_id: str, updates: PersonaUpdate) -> Persona | None:
        existing = self.get_persona(persona_id)
        if existing is None:
            return None
        updated = existing.model_copy(update=updates.model_dump(exclude_none=True))
        updated.updated_at = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    "UPDATE personas SET persona_json = %s, updated_at = %s WHERE persona_id = %s",
                    (_jsonb_payload(updated), updated.updated_at, persona_id),
                )
        return updated

    def delete_persona(self, persona_id: str) -> bool:
        with self._get_pool().connection() as conn:
            with conn.transaction():
                cursor = conn.execute("DELETE FROM personas WHERE persona_id = %s", (persona_id,))
        return cursor.rowcount > 0

    def create_task(self, task: Task) -> Task:
        now = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO tasks (task_id, task_json, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (task_id) DO NOTHING
                    """,
                    (task.id, _jsonb_payload(task), task.created_at, now),
                )
        return self.get_task(task.id)  # type: ignore[return-value]

    def get_task(self, task_id: str) -> Task | None:
        with self._get_pool().connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,)).fetchone()
        if row is None:
            return None
        task = _model_from_payload(Task, row["task_json"])
        return Task(
            id=row["task_id"],
            **task.model_dump(exclude={"id", "created_at", "updated_at"}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_tasks(self) -> list[Task]:
        with self._get_pool().connection() as conn:
            rows = conn.execute("SELECT task_id FROM tasks ORDER BY created_at").fetchall()
        return [self.get_task(row["task_id"]) for row in rows]  # type: ignore[misc]

    def update_task(self, task_id: str, updates: TaskUpdate) -> Task | None:
        existing = self.get_task(task_id)
        if existing is None:
            return None
        updated = existing.model_copy(update=updates.model_dump(exclude_none=True))
        updated.updated_at = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    "UPDATE tasks SET task_json = %s, updated_at = %s WHERE task_id = %s",
                    (_jsonb_payload(updated), updated.updated_at, task_id),
                )
        return updated

    def delete_task(self, task_id: str) -> bool:
        with self._get_pool().connection() as conn:
            with conn.transaction():
                cursor = conn.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
        return cursor.rowcount > 0

    def create_knowledge_item(self, item: KnowledgeItem) -> KnowledgeItem:
        now = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO knowledge_items (item_id, source_type, item_json, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (item_id) DO NOTHING
                    """,
                    (item.id, item.source_type, _jsonb_payload(item), item.created_at, now),
                )
        return self.get_knowledge_item(item.id)  # type: ignore[return-value]

    def get_knowledge_item(self, item_id: str) -> KnowledgeItem | None:
        with self._get_pool().connection() as conn:
            row = conn.execute("SELECT * FROM knowledge_items WHERE item_id = %s", (item_id,)).fetchone()
        if row is None:
            return None
        item = _model_from_payload(KnowledgeItem, row["item_json"])
        return KnowledgeItem(
            id=row["item_id"],
            **item.model_dump(exclude={"id", "created_at", "updated_at"}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_knowledge_items(self, source_type: str | None = None) -> list[KnowledgeItem]:
        with self._get_pool().connection() as conn:
            if source_type is not None:
                rows = conn.execute(
                    "SELECT item_id FROM knowledge_items WHERE source_type = %s ORDER BY created_at",
                    (source_type,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT item_id FROM knowledge_items ORDER BY created_at").fetchall()
        return [self.get_knowledge_item(row["item_id"]) for row in rows]  # type: ignore[misc]

    def update_knowledge_item(self, item_id: str, updates: KnowledgeItemUpdate) -> KnowledgeItem | None:
        existing = self.get_knowledge_item(item_id)
        if existing is None:
            return None
        updated = existing.model_copy(update=updates.model_dump(exclude_none=True))
        updated.updated_at = utc_now()
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute(
                    "UPDATE knowledge_items SET item_json = %s, updated_at = %s WHERE item_id = %s",
                    (_jsonb_payload(updated), updated.updated_at, item_id),
                )
        return updated

    def delete_knowledge_item(self, item_id: str) -> bool:
        with self._get_pool().connection() as conn:
            with conn.transaction():
                cursor = conn.execute("DELETE FROM knowledge_items WHERE item_id = %s", (item_id,))
        return cursor.rowcount > 0

    def clear(self) -> None:
        with self._get_pool().connection() as conn:
            with conn.transaction():
                conn.execute("DELETE FROM knowledge_items")
                conn.execute("DELETE FROM tasks")
                conn.execute("DELETE FROM personas")

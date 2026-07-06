from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

import backend.stores as stores_mod
from backend.core import config
from backend.stores.in_memory_entity_store import InMemoryEntityStore
from backend.stores.in_memory_run_store import InMemoryRunStore
from backend.stores.postgres_entity_store import PostgresEntityStore
from backend.stores.postgres_run_store import PostgresRunStore
from backend.stores.sqlite_entity_store import SqliteEntityStore
from backend.stores.sqlite_run_store import SqliteRunStore


@pytest.fixture(autouse=True)
def reset_store_state() -> None:
    stores_mod._reset_run_store()
    stores_mod._reset_entity_store()
    config.get_settings.cache_clear()
    yield
    stores_mod._reset_run_store()
    stores_mod._reset_entity_store()
    stores_mod._run_store = InMemoryRunStore()
    stores_mod._entity_store = InMemoryEntityStore()
    config.get_settings.cache_clear()


def test_resolve_database_backend() -> None:
    assert config.resolve_database_backend(":memory:") == "memory"
    assert config.resolve_database_backend("postgresql://user:pass@localhost/db") == "postgres"
    assert config.resolve_database_backend("postgres://user:pass@localhost/db") == "postgres"
    assert config.resolve_database_backend("data/synthetic_user_lab.db") == "sqlite"


def test_get_settings_keeps_postgres_dsn_as_string(monkeypatch: pytest.MonkeyPatch) -> None:
    dsn = "postgresql://user:pass@localhost:5432/synthetic_user_lab"
    monkeypatch.setenv("SYNTHETIC_USER_LAB_DATABASE_URL", dsn)
    config.get_settings.cache_clear()

    settings = config.get_settings()

    assert settings.database_url == dsn
    assert isinstance(settings.database_url, str)


def test_get_run_store_returns_inmemory_for_memory_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTHETIC_USER_LAB_DATABASE_URL", ":memory:")
    config.get_settings.cache_clear()

    store = stores_mod.get_run_store()

    assert isinstance(store, InMemoryRunStore)


def test_get_entity_store_returns_sqlite_for_file_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "factory.db"
    monkeypatch.setenv("SYNTHETIC_USER_LAB_DATABASE_URL", str(db_path))
    config.get_settings.cache_clear()

    store = stores_mod.get_entity_store()

    assert isinstance(store, SqliteEntityStore)
    assert db_path.parent.exists()


def test_get_run_store_returns_sqlite_for_file_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "factory.db"
    monkeypatch.setenv("SYNTHETIC_USER_LAB_DATABASE_URL", str(db_path))
    config.get_settings.cache_clear()

    store = stores_mod.get_run_store()

    assert isinstance(store, SqliteRunStore)
    assert db_path.exists()


def test_get_run_store_returns_postgres_for_postgres_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTHETIC_USER_LAB_DATABASE_URL", "postgresql://user:pass@localhost:5432/synthetic_user_lab")
    config.get_settings.cache_clear()

    with patch.object(PostgresRunStore, "initialize", autospec=True, return_value=None):
        store = stores_mod.get_run_store()

    assert isinstance(store, PostgresRunStore)


def test_get_entity_store_returns_postgres_for_postgres_dsn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTHETIC_USER_LAB_DATABASE_URL", "postgresql://user:pass@localhost:5432/synthetic_user_lab")
    config.get_settings.cache_clear()

    with patch.object(PostgresEntityStore, "initialize", autospec=True, return_value=None):
        store = stores_mod.get_entity_store()

    assert isinstance(store, PostgresEntityStore)

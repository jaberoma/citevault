"""SQLite connection & schema-init tests."""

from pathlib import Path

import pytest

from citevault.adapters.outbound.sqlite.connection import open_db


def test_open_db_creates_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = open_db(str(db_path))
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [r[0] for r in cur.fetchall()]
    assert "sources" in tables
    assert "spans" in tables
    assert "structured_entries" in tables
    assert "spans_fts" in tables
    assert "spans_vec" in tables


def test_open_db_loads_sqlite_vec(tmp_path: Path) -> None:
    db_path = tmp_path / "vec.db"
    conn = open_db(str(db_path))
    result = conn.execute("SELECT vec_version()").fetchone()
    assert result is not None


def test_open_db_sets_user_version_on_new_db(tmp_path: Path) -> None:
    db_path = tmp_path / "uv.db"
    conn = open_db(str(db_path))
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == 1


def test_open_db_enables_wal_mode(tmp_path: Path) -> None:
    conn = open_db(str(tmp_path / "wal.db"))
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"


def test_open_db_skips_schema_on_existing_db(tmp_path: Path) -> None:
    """Second open must not wipe data and must leave user_version intact."""
    db_path = tmp_path / "existing.db"
    conn = open_db(str(db_path))
    conn.execute(
        "INSERT INTO sources (id, kind, path, text, created_at) VALUES ('x','note','p','t','2026-01-01')"
    )
    conn.commit()
    conn.close()

    conn2 = open_db(str(db_path))
    row = conn2.execute("SELECT id FROM sources WHERE id='x'").fetchone()
    assert row is not None, "open_db wiped existing data on second open"
    version = conn2.execute("PRAGMA user_version").fetchone()[0]
    assert version == 1

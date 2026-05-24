"""SqliteEvidenceRepository.delete_source tests."""

from pathlib import Path

from citevault.adapters.outbound.sqlite.connection import open_db
from citevault.adapters.outbound.sqlite_repo import SqliteEvidenceRepository
from citevault.domain.models import Source, SourceKind, Span
import datetime


def _make_repo(tmp_path: Path) -> SqliteEvidenceRepository:
    return SqliteEvidenceRepository(str(tmp_path / "t.db"))


def test_delete_source_removes_source_and_spans(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    src = Source(
        id="src-1", kind=SourceKind.NOTE, path="/p/note.md", text="hello",
        created_at=datetime.datetime(2026, 1, 1),
    )
    span = Span(id="sp-1", source_id="src-1", start_offset=0, end_offset=5, text="hello")
    repo.save_source(src)
    repo.save_span(span, embedding=[0.1] * 384)

    assert len(repo.list_sources()) == 1
    repo.delete_source("src-1")
    assert repo.list_sources() == []
    assert repo.get_span("sp-1") is None


def test_delete_nonexistent_source_is_noop(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    repo.delete_source("does-not-exist")  # must not raise
    assert repo.list_sources() == []


def test_delete_source_cleans_virtual_tables(tmp_path: Path) -> None:
    """CASCADE does not reach FTS/vec virtual tables — delete_source must clean them explicitly."""
    repo = _make_repo(tmp_path)
    src = Source(
        id="src-1", kind=SourceKind.NOTE, path="/p.md", text="hello",
        created_at=datetime.datetime(2026, 1, 1),
    )
    span = Span(id="sp-1", source_id="src-1", start_offset=0, end_offset=5, text="hello")
    repo.save_source(src)
    repo.save_span(span, embedding=[0.1] * 384)

    fts_before = repo._conn.execute(
        "SELECT count(*) FROM spans_fts WHERE span_id = ?", ("sp-1",)
    ).fetchone()[0]
    vec_before = repo._conn.execute(
        "SELECT count(*) FROM spans_vec WHERE span_id = ?", ("sp-1",)
    ).fetchone()[0]
    assert fts_before == 1
    assert vec_before == 1

    repo.delete_source("src-1")

    fts_after = repo._conn.execute(
        "SELECT count(*) FROM spans_fts WHERE span_id = ?", ("sp-1",)
    ).fetchone()[0]
    vec_after = repo._conn.execute(
        "SELECT count(*) FROM spans_vec WHERE span_id = ?", ("sp-1",)
    ).fetchone()[0]
    assert fts_after == 0, "spans_fts rows not cleaned after delete_source"
    assert vec_after == 0, "spans_vec rows not cleaned after delete_source"

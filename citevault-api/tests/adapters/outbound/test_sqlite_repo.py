"""SqliteEvidenceRepository tests."""

from datetime import datetime
from pathlib import Path

from citevault.adapters.outbound.sqlite_repo import SqliteEvidenceRepository
from citevault.domain.models import Job, Source, SourceKind, Span


def test_save_and_list_source(tmp_path: Path) -> None:
    repo = SqliteEvidenceRepository(str(tmp_path / "t.db"))
    src = Source(id="s1", kind=SourceKind.RESUME_MASTER, path="r.md",
                 text="hello", created_at=datetime(2026, 5, 11))
    repo.save_source(src)
    sources = repo.list_sources()
    assert len(sources) == 1
    assert sources[0].id == "s1"


def test_save_span_and_lookup(tmp_path: Path) -> None:
    repo = SqliteEvidenceRepository(str(tmp_path / "t.db"))
    src = Source(id="s1", kind=SourceKind.NOTE, path="n.md",
                 text="hello world", created_at=datetime(2026, 5, 11))
    repo.save_source(src)
    sp = Span(id="sp1", source_id="s1", start_offset=0, end_offset=5, text="hello")
    repo.save_span(sp, embedding=[0.1] * 384)
    fetched = repo.get_span("sp1")
    assert fetched is not None
    assert fetched.text == "hello"


def test_save_structured_entry_job(tmp_path: Path) -> None:
    repo = SqliteEvidenceRepository(str(tmp_path / "t.db"))
    src = Source(id="s1", kind=SourceKind.RESUME_MASTER, path="r.md",
                 text="", created_at=datetime(2026, 5, 11))
    repo.save_source(src)
    job = Job(id="job-1", source_id="s1", company="TechCorp",
              role="Engineer", start_date="2021-01",
              bullets=["Built things."], evidence_span_ids=[])
    repo.save_structured_entry(job)
    entries = repo.list_structured_entries("s1")
    assert len(entries) == 1
    assert isinstance(entries[0], Job)
    assert entries[0].company == "TechCorp"

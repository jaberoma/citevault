"""IndexEvidence use case tests using fakes."""

from pathlib import Path

from citevault.application.index_evidence import IndexEvidence
from citevault.domain.models import Job
from tests.fakes import FakeEmbedding, FakeEvidenceRepository


def test_index_evidence_creates_sources_and_spans(tmp_path: Path) -> None:
    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    (ev_dir / "blog.md").write_text("First paragraph.\n\nSecond paragraph.")
    repo = FakeEvidenceRepository()
    use_case = IndexEvidence(repo=repo, embedder=FakeEmbedding())
    report = use_case.run(str(ev_dir))
    assert report.sources_indexed == 1
    assert report.spans_indexed >= 1
    assert repo.sources[0].kind.value == "note"


def test_index_master_resume_produces_structured_entries(tmp_path: Path) -> None:
    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    (ev_dir / "master_resume.md").write_text(
        "# Experience\n\n## Engineer · TechCo · 2020-01 – present\n- Did things.\n"
    )
    repo = FakeEvidenceRepository()
    use_case = IndexEvidence(repo=repo, embedder=FakeEmbedding())
    report = use_case.run(str(ev_dir))
    assert report.structured_entries_indexed >= 1
    assert any(isinstance(e, Job) for e in repo.structured_entries)


def test_subdirectory_in_folder_is_skipped(tmp_path: Path) -> None:
    ev_dir = tmp_path / "evidence"
    ev_dir.mkdir()
    (ev_dir / "notes.md").write_text("Some notes.")
    (ev_dir / "subdir").mkdir()
    repo = FakeEvidenceRepository()
    use_case = IndexEvidence(repo=repo, embedder=FakeEmbedding())
    report = use_case.run(str(ev_dir))
    assert report.sources_indexed == 1

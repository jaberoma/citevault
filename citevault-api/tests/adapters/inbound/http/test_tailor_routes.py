"""Tailor routes — submit + retrieve."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from citevault.adapters.inbound.http.app import create_app
from citevault.application.tailor_resume import TailoringResult
from citevault.composition.container import Container
from citevault.domain.models import GapReport, JobPosting
from citevault.domain.services.metrics_calculator import CaseRunSummary
from tests.fakes import FakeEvidenceRepository, FakeLLM, FakeReranker, FakeRetrieval


def _fake_result() -> TailoringResult:
    return TailoringResult(
        tailoring_id="t-test",
        job_posting=JobPosting(id="jp-test", raw_text="test", role_title="Test Role"),
        verified_claims=[],
        gap_report=GapReport(tailoring_id="t-test", entries=[]),
        summary=CaseRunSummary(0, 0, 0, 0, 0, 0),
    )


def _fake_container(llm: FakeLLM | None = None) -> MagicMock:
    mock_c = MagicMock()
    mock_c.llm = llm or FakeLLM()
    mock_c.retrieval = FakeRetrieval()
    mock_c.reranker = FakeReranker()
    mock_c.evidence_repo = FakeEvidenceRepository()
    mock_c.tailor_resume.run.return_value = _fake_result()
    return mock_c


def test_post_tailor_returns_tailoring_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    app.state.container = _fake_container()
    with TestClient(app) as client:
        r = client.post("/api/tailor", json={"job_posting": "Hi"})
        assert r.status_code == 202
        assert "tailoring_id" in r.json()


def test_get_tailoring_404_for_unknown_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    app.state.container = MagicMock(spec=Container)
    with TestClient(app) as client:
        r = client.get("/api/tailor/nonexistent")
        assert r.status_code == 404


def test_naive_compare_stored_when_requested(tmp_path: Path, monkeypatch) -> None:
    """When naive_compare=True the background thread calls llm.complete and stores naive_md."""
    from unittest.mock import patch as _patch
    from citevault.domain.models import JobPosting

    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    llm = FakeLLM(responses=["naive resume here"])
    mock_c = _fake_container(llm=llm)
    app.state.container = mock_c

    fake_posting = JobPosting(id="jp-1", raw_text="test", role_title="Backend Engineer")

    with _patch("citevault.adapters.inbound.http.tailor_routes.JobPostingParser") as MockParser, \
         _patch("citevault.adapters.inbound.http.tailor_routes.CoverLetterComposer") as MockCover, \
         _patch("citevault.adapters.inbound.http.tailor_routes.render_resume_markdown", return_value=""), \
         _patch("citevault.adapters.inbound.http.tailor_routes.render_gaps_markdown", return_value=""):
        MockParser.return_value.parse.return_value = fake_posting
        MockCover.return_value.compose.return_value = "Dear Hiring Manager"
        with TestClient(app) as client:
            r = client.post("/api/tailor", json={"job_posting": "test", "naive_compare": True})
            assert r.status_code == 202
            tid = r.json()["tailoring_id"]

        # Background thread is a daemon; give it time to complete.
        from citevault.adapters.inbound.http.tailor_routes import _STORE
        deadline = time.time() + 3.0
        while time.time() < deadline and _STORE.get(tid, {}).get("status") == "running":
            time.sleep(0.05)

    assert _STORE.get(tid, {}).get("naive_md") is not None


def test_naive_compare_includes_evidence_in_prompt(tmp_path: Path, monkeypatch) -> None:
    """naive_compare=True must pass indexed evidence spans to the LLM prompt."""
    from unittest.mock import patch as _patch
    from citevault.domain.models import Source, SourceKind, Span

    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    llm = FakeLLM(responses=["naive resume here"])
    mock_c = _fake_container(llm=llm)

    src = Source(id="src-1", kind=SourceKind.RESUME_MASTER, path="master_resume.md", text="full doc")
    span = Span(id="sp-1", source_id="src-1", start_offset=0, end_offset=38, text="Built REST APIs in Go serving 80k DAU.")
    mock_c.evidence_repo.save_source(src)
    mock_c.evidence_repo.save_span(span, [0.0] * 384)
    app.state.container = mock_c

    fake_posting = JobPosting(id="jp-1", raw_text="test", role_title="Backend Engineer")

    with _patch("citevault.adapters.inbound.http.tailor_routes.JobPostingParser") as MockParser, \
         _patch("citevault.adapters.inbound.http.tailor_routes.CoverLetterComposer") as MockCover, \
         _patch("citevault.adapters.inbound.http.tailor_routes.render_resume_markdown", return_value=""), \
         _patch("citevault.adapters.inbound.http.tailor_routes.render_gaps_markdown", return_value=""):
        MockParser.return_value.parse.return_value = fake_posting
        MockCover.return_value.compose.return_value = "Dear Hiring Manager"
        with TestClient(app) as client:
            r = client.post("/api/tailor", json={"job_posting": "test", "naive_compare": True})
            assert r.status_code == 202
            tid = r.json()["tailoring_id"]

        from citevault.adapters.inbound.http.tailor_routes import _STORE
        deadline = time.time() + 3.0
        while time.time() < deadline and _STORE.get(tid, {}).get("status") == "running":
            time.sleep(0.05)

    assert llm.calls, "Expected at least one LLM call for naive compare"
    naive_prompt = llm.calls[0]["prompt"]
    assert "Built REST APIs in Go serving 80k DAU." in naive_prompt
    assert "master_resume.md" in naive_prompt


def test_pdf_endpoint_returns_404_for_unknown(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    app.state.container = _fake_container()
    with TestClient(app) as client:
        r = client.get("/api/tailor/nonexistent/pdf")
    assert r.status_code == 404


def test_pdf_endpoint_returns_404_while_running(tmp_path: Path, monkeypatch) -> None:
    import citevault.adapters.inbound.http.tailor_routes as routes
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    app.state.container = _fake_container()
    routes._STORE.clear()
    routes._STORE["t-running"] = {"status": "running"}
    with TestClient(app) as client:
        r = client.get("/api/tailor/t-running/pdf")
    assert r.status_code == 404


def test_pdf_endpoint_serves_file_when_ready(tmp_path: Path, monkeypatch) -> None:
    import citevault.adapters.inbound.http.tailor_routes as routes
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    pdf_file = tmp_path / "t-done.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake")
    app = create_app()
    app.state.container = _fake_container()
    routes._STORE.clear()
    routes._STORE["t-done"] = {"status": "complete", "pdf_path": str(pdf_file), "pdf_ready": True}
    with TestClient(app) as client:
        r = client.get("/api/tailor/t-done/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


def test_naive_compare_timeout_degrades_gracefully(tmp_path: Path, monkeypatch) -> None:
    """If the naive comparison LLM call times out, tailoring must still complete — not error."""
    import httpx
    from unittest.mock import patch as _patch
    from citevault.domain.models import JobPosting

    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    # complete() raises ReadTimeout only on the naive call (after tailor_resume.run succeeds)
    llm = FakeLLM(responses=[])
    llm.complete = MagicMock(side_effect=httpx.ReadTimeout("timed out"))
    mock_c = _fake_container(llm=llm)
    app.state.container = mock_c

    fake_posting = JobPosting(id="jp-1", raw_text="test", role_title="Backend Engineer")

    with _patch("citevault.adapters.inbound.http.tailor_routes.JobPostingParser") as MockParser, \
         _patch("citevault.adapters.inbound.http.tailor_routes.CoverLetterComposer") as MockCover, \
         _patch("citevault.adapters.inbound.http.tailor_routes.render_resume_markdown", return_value=""), \
         _patch("citevault.adapters.inbound.http.tailor_routes.render_gaps_markdown", return_value=""):
        MockParser.return_value.parse.return_value = fake_posting
        MockCover.return_value.compose.return_value = "Dear Hiring Manager"
        with TestClient(app) as client:
            r = client.post("/api/tailor", json={"job_posting": "test", "naive_compare": True})
            assert r.status_code == 202
            tid = r.json()["tailoring_id"]

        from citevault.adapters.inbound.http.tailor_routes import _STORE
        deadline = time.time() + 3.0
        while time.time() < deadline and _STORE.get(tid, {}).get("status") == "running":
            time.sleep(0.05)

    assert _STORE.get(tid, {}).get("status") == "complete", \
        f"Expected status=complete but got: {_STORE.get(tid, {}).get('status')}"


def test_store_evicts_oldest_when_over_100(tmp_path: Path, monkeypatch) -> None:
    """_STORE must not grow beyond 100 entries; oldest are evicted first."""
    import citevault.adapters.inbound.http.tailor_routes as routes

    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    app.state.container = _fake_container()

    # Reset the module-level store so this test is isolation-safe.
    routes._STORE.clear()

    with TestClient(app) as client:
        # Fill to exactly 100.
        for i in range(100):
            routes._STORE[f"t-stale{i:04d}"] = {"status": "complete"}
        assert len(routes._STORE) == 100

        # 101st entry triggers eviction.
        r = client.post("/api/tailor", json={"job_posting": "test"})
        assert r.status_code == 202

        new_id = r.json()["tailoring_id"]
        deadline = time.time() + 3.0
        while time.time() < deadline and routes._STORE.get(new_id, {}).get("status") == "running":
            time.sleep(0.05)

    assert len(routes._STORE) <= 100

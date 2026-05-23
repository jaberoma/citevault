"""Evidence routes."""

from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from citevault.adapters.inbound.http.app import create_app
from citevault.composition.container import Container
from tests.fakes import FakeEmbedding


def _app_with_fake_container(tmp_path: Path, monkeypatch) -> object:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    mock_container = MagicMock(spec=Container)
    mock_container.embedder = FakeEmbedding()
    app.state.container = mock_container
    return app


def test_list_evidence_empty(tmp_path: Path, monkeypatch) -> None:
    app = _app_with_fake_container(tmp_path, monkeypatch)
    with TestClient(app) as client:
        r = client.get("/api/evidence")
    assert r.status_code == 200
    assert r.json() == {"sources": []}


def test_upload_source_returns_source_id(tmp_path: Path, monkeypatch) -> None:
    app = _app_with_fake_container(tmp_path, monkeypatch)
    with TestClient(app) as client:
        files = {"file": ("note.md", b"Hello world.\n\nSecond para.", "text/markdown")}
        r = client.post("/api/evidence/source", files=files)
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["kind"] == "note"

        r2 = client.get("/api/evidence")
        assert len(r2.json()["sources"]) == 1


def test_delete_source(tmp_path: Path, monkeypatch) -> None:
    app = _app_with_fake_container(tmp_path, monkeypatch)
    with TestClient(app) as client:
        files = {"file": ("note.md", b"hi", "text/markdown")}
        sid = client.post("/api/evidence/source", files=files).json()["id"]
        r = client.delete(f"/api/evidence/source/{sid}")
        assert r.status_code == 204
        assert client.get("/api/evidence").json()["sources"] == []

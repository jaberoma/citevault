"""Ollama proxy routes tests."""

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from citevault.adapters.inbound.http.app import create_app


@respx.mock
def test_list_models_returns_downloaded_models(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.get("http://localhost:11434/api/tags").mock(
        return_value=httpx.Response(200, json={
            "models": [
                {"name": "gemma4:e4b", "size": 9608350718,
                 "details": {"family": "gemma4"}}
            ]
        })
    )
    client = TestClient(create_app())
    r = client.get("/api/ollama/models")
    assert r.status_code == 200
    models = r.json()["models"]
    assert len(models) == 1
    assert models[0]["name"] == "gemma4:e4b"
    assert models[0]["size"] == 9608350718
    assert models[0]["family"] == "gemma4"


@respx.mock
def test_list_models_returns_empty_when_ollama_unreachable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.get("http://localhost:11434/api/tags").mock(
        side_effect=httpx.ConnectError("unreachable")
    )
    client = TestClient(create_app())
    r = client.get("/api/ollama/models")
    assert r.status_code == 200
    assert r.json() == {"models": []}

"""Settings GET / PUT roundtrip."""

from pathlib import Path

import httpx
import respx
from fastapi.testclient import TestClient

from citevault.adapters.inbound.http.app import create_app


def test_settings_get_returns_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    client = TestClient(create_app())
    r = client.get("/api/settings")
    assert r.status_code == 200
    assert r.json()["model"]


@respx.mock
def test_settings_put_updates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.post("http://localhost:11434/api/show").mock(
        return_value=httpx.Response(200, json={"details": {"family": "gemma"}})
    )
    client = TestClient(create_app())
    r = client.put("/api/settings", json={"model": "gemma4:27b"})
    assert r.status_code == 200
    assert client.get("/api/settings").json()["model"] == "gemma4:27b"


@respx.mock
def test_get_settings_includes_available_true(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.post("http://localhost:11434/api/show").mock(
        return_value=httpx.Response(200, json={"details": {"family": "gemma"}})
    )
    client = TestClient(create_app())
    r = client.get("/api/settings")
    assert r.status_code == 200
    assert r.json()["available"] is True


@respx.mock
def test_get_settings_includes_available_false_when_model_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.post("http://localhost:11434/api/show").mock(
        return_value=httpx.Response(404, json={"error": "model 'gemma4:e4b' not found"})
    )
    client = TestClient(create_app())
    r = client.get("/api/settings")
    assert r.status_code == 200
    assert r.json()["available"] is False


@respx.mock
def test_put_settings_rejects_unknown_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.post("http://localhost:11434/api/show").mock(
        return_value=httpx.Response(404, json={"error": "model 'bad:v1' not found"})
    )
    client = TestClient(create_app())
    r = client.put("/api/settings", json={"model": "bad:v1"})
    assert r.status_code == 422
    assert "bad:v1" in r.json()["detail"]
    assert "ollama pull" in r.json()["detail"]


@respx.mock
def test_put_settings_accepts_known_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    respx.post("http://localhost:11434/api/show").mock(
        return_value=httpx.Response(200, json={"details": {"family": "gemma"}})
    )
    client = TestClient(create_app())
    r = client.put("/api/settings", json={"model": "gemma4:27b"})
    assert r.status_code == 200
    assert r.json()["model"] == "gemma4:27b"
    assert r.json()["available"] is True

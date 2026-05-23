"""FastAPI health endpoint and app lifecycle."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from citevault.adapters.inbound.http.app import create_app
from citevault.composition.container import Container


def test_health_returns_ok() -> None:
    app = create_app()
    mock_c = MagicMock()
    mock_c.is_ready = True
    app.state.container = mock_c
    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_returns_loading_when_not_ready() -> None:
    app = create_app()
    mock_c = MagicMock()
    mock_c.is_ready = False
    app.state.container = mock_c
    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "loading"}


def test_lifespan_creates_container_singleton(tmp_path, monkeypatch) -> None:
    """Container must be built once at startup and stored on app.state."""
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    with patch("citevault.adapters.inbound.http.app.Container") as MockContainer:
        MockContainer.return_value = MagicMock(spec=Container)
        with TestClient(app) as client:
            client.get("/api/health")
        MockContainer.assert_called_once()
        assert hasattr(app.state, "container")


def test_cors_allows_any_origin_by_default(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("CITEVAULT_CORS_ORIGINS", raising=False)
    app = create_app()
    mock_c = MagicMock()
    mock_c.is_ready = True
    app.state.container = mock_c
    with TestClient(app) as client:
        r = client.options(
            "/api/health",
            headers={"Origin": "http://anyhost.example", "Access-Control-Request-Method": "GET"},
        )
    assert r.headers.get("access-control-allow-origin") in ("*", "http://anyhost.example")


def test_cors_respects_env_override(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CITEVAULT_CORS_ORIGINS", "http://myapp.local,http://other.local")
    app = create_app()
    mock_c = MagicMock()
    mock_c.is_ready = True
    app.state.container = mock_c
    with TestClient(app) as client:
        r = client.options(
            "/api/health",
            headers={"Origin": "http://myapp.local", "Access-Control-Request-Method": "GET"},
        )
    assert r.headers.get("access-control-allow-origin") == "http://myapp.local"


def test_lifespan_respects_pre_set_container(tmp_path, monkeypatch) -> None:
    """Tests can pre-set app.state.container to bypass real model loading."""
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    app = create_app()
    sentinel = MagicMock(spec=Container)
    app.state.container = sentinel
    with patch("citevault.adapters.inbound.http.app.Container") as MockContainer:
        with TestClient(app) as client:
            client.get("/api/health")
        MockContainer.assert_not_called()
    assert app.state.container is sentinel

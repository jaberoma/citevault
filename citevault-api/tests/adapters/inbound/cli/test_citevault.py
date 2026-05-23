"""CLI entry-point tests."""

from unittest.mock import patch

from typer.testing import CliRunner

from citevault.adapters.inbound.cli.citevault import app


def test_cli_version_exits_successfully() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "citevault" in result.stdout.lower()
    assert "0.1.0" in result.stdout


def test_serve_command_starts_uvicorn() -> None:
    runner = CliRunner()
    with patch("uvicorn.run") as mock_run:
        result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "9000"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs.get("host") == "127.0.0.1"
    assert kwargs.get("port") == 9000

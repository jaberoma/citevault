"""CLI `citevault tailor` end-to-end smoke test (requires running Ollama)."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from citevault.adapters.inbound.cli.citevault import app


@pytest.mark.skipif(
    os.environ.get("CITEVAULT_SMOKE") != "1",
    reason="Smoke test; set CITEVAULT_SMOKE=1 to run against real Ollama.",
)
def test_tailor_command_produces_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ev = tmp_path / "evidence"
    ev.mkdir()
    (ev / "master_resume.md").write_text(
        "# Experience\n\n## Engineer · TechCo · 2020-01 – present\n"
        "- Built backend services in Python.\n"
    )
    job = tmp_path / "job.txt"
    job.write_text("We need a Python backend engineer.")
    out = tmp_path / "out"

    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "t.db"))
    runner = CliRunner()
    assert runner.invoke(app, ["index", str(ev)]).exit_code == 0
    result = runner.invoke(app, ["tailor", str(job), "--output", str(out)])
    assert result.exit_code == 0
    assert (out / "resume.md").exists()
    assert (out / "resume.pdf").exists()
    assert (out / "gaps.md").exists()


def test_tailor_command_is_registered() -> None:
    """Verify the command exists in the CLI (doesn't need Ollama)."""
    runner = CliRunner()
    result = runner.invoke(app, ["tailor", "--help"])
    assert result.exit_code == 0
    assert "tailor" in result.stdout.lower() or "job" in result.stdout.lower()


def test_tailor_nonexistent_file_exits_with_error() -> None:
    """Passing a non-existent file must exit with a non-zero code, no unhandled traceback."""
    runner = CliRunner()
    result = runner.invoke(app, ["tailor", "/nonexistent/path/job.txt"])
    assert result.exit_code != 0
    # Ensure no raw Python traceback leaked — only a user-friendly message
    assert "Traceback" not in (result.output or "")
    assert result.exception is None or isinstance(result.exception, SystemExit)

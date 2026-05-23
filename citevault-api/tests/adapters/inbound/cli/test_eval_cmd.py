"""CLI `citevault eval` smoke test."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from citevault.adapters.inbound.cli.citevault import app


@pytest.mark.skipif(
    os.environ.get("CITEVAULT_SMOKE") != "1",
    reason="Smoke test against real Ollama; set CITEVAULT_SMOKE=1 to run.",
)
def test_eval_command_runs_golden_set(tmp_path: Path, monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[5]
    monkeypatch.setenv("CITEVAULT_DB", str(tmp_path / "eval.db"))
    runner = CliRunner()
    result = runner.invoke(app, ["eval", "--golden", str(repo_root / "golden")])
    assert "First-Pass Grounding" in result.stdout
    assert "case_01" in result.stdout

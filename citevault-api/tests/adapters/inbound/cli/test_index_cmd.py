"""CLI `citevault index` smoke test."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from citevault.adapters.inbound.cli.citevault import app


def test_index_command_indexes_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ev = tmp_path / "evidence"
    ev.mkdir()
    (ev / "note.md").write_text("Hello world.")
    db = tmp_path / "t.db"
    monkeypatch.setenv("CITEVAULT_DB", str(db))

    runner = CliRunner()
    result = runner.invoke(app, ["index", str(ev)])
    assert result.exit_code == 0, result.stdout
    assert "Indexed" in result.stdout
    assert db.exists()

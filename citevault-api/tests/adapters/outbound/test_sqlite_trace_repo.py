"""SqliteTraceRepository tests."""

import json
from pathlib import Path

from citevault.adapters.outbound.sqlite_repo import SqliteTraceRepository


def test_save_and_load_trace(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    repo = SqliteTraceRepository(db_path)
    
    trace_id = "t1"
    trace_data = {"event": "tailoring_started", "data": "..."}
    trace_json = json.dumps(trace_data)
    
    repo.save_trace(trace_json, trace_id)
    
    loaded = repo.load_trace(trace_id)
    assert loaded == trace_json
    assert json.loads(loaded)["event"] == "tailoring_started"


def test_load_nonexistent_trace(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    repo = SqliteTraceRepository(db_path)
    assert repo.load_trace("nonexistent") is None

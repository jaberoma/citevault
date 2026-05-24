"""SQLite-backed EvidenceRepository adapter."""

from __future__ import annotations

import json
import struct
from datetime import datetime, timezone

from citevault.adapters.outbound.sqlite.connection import open_db
from citevault.domain.models import (
    Achievement, Job, Project, Skill, Source, SourceKind, Span,
)


def _pack_floats(values: list[float]) -> bytes:
    return struct.pack(f"{len(values)}f", *values)


class SqliteEvidenceRepository:
    def __init__(self, db_path: str) -> None:
        self._conn = open_db(db_path)

    def save_source(self, source: Source) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?)",
            (source.id, source.kind.value, source.path, source.text,
             source.created_at.isoformat()),
        )
        self._conn.commit()

    def save_span(self, span: Span, embedding: list[float]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO spans VALUES (?, ?, ?, ?, ?)",
            (span.id, span.source_id, span.start_offset, span.end_offset, span.text),
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO spans_fts (span_id, text) VALUES (?, ?)",
            (span.id, span.text),
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO spans_vec (span_id, embedding) VALUES (?, ?)",
            (span.id, _pack_floats(embedding)),
        )
        self._conn.commit()

    def save_structured_entry(
        self, entry: Job | Project | Skill | Achievement,
    ) -> None:
        entry_type = type(entry).__name__.lower()
        payload = entry.model_dump_json()
        self._conn.execute(
            "INSERT OR REPLACE INTO structured_entries VALUES (?, ?, ?, ?)",
            (entry.id, entry.source_id, entry_type, payload),
        )
        self._conn.commit()

    def list_sources(self) -> list[Source]:
        cur = self._conn.execute("SELECT id, kind, path, text, created_at FROM sources")
        return [
            Source(id=r[0], kind=SourceKind(r[1]), path=r[2], text=r[3],
                   created_at=datetime.fromisoformat(r[4]))
            for r in cur.fetchall()
        ]

    def get_span(self, span_id: str) -> Span | None:
        cur = self._conn.execute(
            "SELECT id, source_id, start_offset, end_offset, text FROM spans WHERE id = ?",
            (span_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Span(id=row[0], source_id=row[1], start_offset=row[2],
                    end_offset=row[3], text=row[4])

    def delete_source(self, source_id: str) -> None:
        # Virtual tables are not reached by CASCADE — must be cleaned explicitly.
        self._conn.execute(
            "DELETE FROM spans_fts WHERE span_id IN (SELECT id FROM spans WHERE source_id = ?)",
            (source_id,),
        )
        self._conn.execute(
            "DELETE FROM spans_vec WHERE span_id IN (SELECT id FROM spans WHERE source_id = ?)",
            (source_id,),
        )
        self._conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        self._conn.commit()

    def list_spans_for_source(self, source_id: str) -> list[Span]:
        cur = self._conn.execute(
            "SELECT id, source_id, start_offset, end_offset, text FROM spans WHERE source_id = ?",
            (source_id,),
        )
        return [
            Span(id=r[0], source_id=r[1], start_offset=r[2], end_offset=r[3], text=r[4])
            for r in cur.fetchall()
        ]

    def list_structured_entries(
        self, source_id: str,
    ) -> list[Job | Project | Skill | Achievement]:
        cur = self._conn.execute(
            "SELECT entry_type, payload_json FROM structured_entries WHERE source_id = ?",
            (source_id,),
        )
        result: list[Job | Project | Skill | Achievement] = []
        for entry_type, payload in cur.fetchall():
            data = json.loads(payload)
            cls = {"job": Job, "project": Project, "skill": Skill,
                   "achievement": Achievement}[entry_type]
            result.append(cls.model_validate(data))  # type: ignore[attr-defined]
        return result


class SqliteTraceRepository:
    def __init__(self, db_path: str) -> None:
        self._conn = open_db(db_path)

    def save_trace(self, trace_json: str, tailoring_id: str) -> None:
        started_at = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            "INSERT OR REPLACE INTO tailoring_traces (id, started_at, trace_json) VALUES (?, ?, ?)",
            (tailoring_id, started_at, trace_json),
        )
        self._conn.commit()

    def load_trace(self, tailoring_id: str) -> str | None:
        cur = self._conn.execute(
            "SELECT trace_json FROM tailoring_traces WHERE id = ?",
            (tailoring_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return str(row[0])

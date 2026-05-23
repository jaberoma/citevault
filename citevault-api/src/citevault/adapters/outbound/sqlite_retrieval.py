"""Hybrid retrieval (BM25 via FTS5 + dense via sqlite-vec) with RRF fusion."""

from __future__ import annotations

import sqlite3
import struct

from citevault.adapters.outbound.sqlite.connection import open_db
from citevault.domain.models import RetrievalCandidate
from citevault.domain.ports import EmbeddingPort


def _fts_escape(query: str) -> str:
    """Wrap query as an FTS5 phrase match to avoid operator injection."""
    return '"' + query.replace('"', '""') + '"'


def _pack(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _rrf(rank_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: each doc gets sum(1 / (k + rank_in_list))."""
    scores: dict[str, float] = {}
    for rl in rank_lists:
        for rank, doc_id in enumerate(rl, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class SqliteRetrieval:
    def __init__(self, db_path: str, embedder: EmbeddingPort) -> None:
        self._conn = open_db(db_path)
        self._embedder = embedder

    def hybrid_search(self, query: str, k: int) -> list[RetrievalCandidate]:
        # BM25 via FTS5 — phrase-escaped to prevent FTS5 operator injection
        try:
            bm25 = [r[0] for r in self._conn.execute(
                "SELECT span_id FROM spans_fts WHERE spans_fts MATCH ? ORDER BY rank LIMIT ?",
                (_fts_escape(query), k * 2),
            ).fetchall()]
        except sqlite3.OperationalError:
            bm25 = []

        # Dense KNN via sqlite-vec vec0 — `WHERE embedding MATCH ? AND k=N`
        qvec = self._embedder.embed([query])[0]
        try:
            dense = [r[0] for r in self._conn.execute(
                "SELECT span_id FROM spans_vec WHERE embedding MATCH ? AND k=?",
                (_pack(qvec), k * 2),
            ).fetchall()]
        except sqlite3.OperationalError:
            dense = []

        fused = _rrf([bm25, dense])[:k]
        result: list[RetrievalCandidate] = []
        for span_id, score in fused:
            row = self._conn.execute(
                "SELECT text FROM spans WHERE id = ?", (span_id,)
            ).fetchone()
            if row is not None:
                result.append(RetrievalCandidate(
                    span_id=span_id, text=row[0], score=float(score),
                ))
        return result

"""Hybrid retrieval over an indexed evidence base."""

from datetime import datetime
from pathlib import Path

from citevault.adapters.outbound.sqlite_repo import SqliteEvidenceRepository
from citevault.adapters.outbound.sqlite_retrieval import SqliteRetrieval
from citevault.adapters.outbound.st_embedding import SentenceTransformersEmbedding
from citevault.domain.models import Source, SourceKind, Span


def test_hybrid_search_returns_relevant_spans(tmp_path: Path) -> None:
    db = str(tmp_path / "t.db")
    repo = SqliteEvidenceRepository(db)
    emb = SentenceTransformersEmbedding()

    src = Source(id="s1", kind=SourceKind.NOTE, path="x.md",
                 text="kubernetes is good. pasta is tasty.",
                 created_at=datetime(2026, 5, 11))
    repo.save_source(src)
    texts = ["Kubernetes is a container orchestrator.",
             "I had pasta with red sauce for dinner."]
    vecs = emb.embed(texts)
    for i, (t, v) in enumerate(zip(texts, vecs)):
        repo.save_span(Span(id=f"sp{i}", source_id="s1",
                            start_offset=0, end_offset=len(t), text=t),
                       embedding=v)

    retr = SqliteRetrieval(db_path=db, embedder=emb)
    results = retr.hybrid_search("container orchestration", k=2)
    assert len(results) >= 1
    assert results[0].text.startswith("Kubernetes")


def test_hybrid_search_empty_db_returns_empty_list(tmp_path: Path) -> None:
    db = str(tmp_path / "empty.db")
    SqliteEvidenceRepository(db)  # create schema only, no spans
    retr = SqliteRetrieval(db_path=db, embedder=SentenceTransformersEmbedding())
    results = retr.hybrid_search("anything", k=5)
    assert results == []

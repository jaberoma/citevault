"""Verify ports are Protocols with the expected signatures."""

from citevault.domain.ports import (
    EmbeddingPort, EvidenceRepository, LLMPort, RerankerPort, RetrievalPort,
    TraceRepository,
)


def test_llm_port_has_complete_method() -> None:
    assert hasattr(LLMPort, "complete")


def test_embedding_port_has_embed_method() -> None:
    assert hasattr(EmbeddingPort, "embed")


def test_reranker_port_has_rerank_method() -> None:
    assert hasattr(RerankerPort, "rerank")


def test_retrieval_port_has_hybrid_search_method() -> None:
    assert hasattr(RetrievalPort, "hybrid_search")


def test_evidence_repository_save_load() -> None:
    assert hasattr(EvidenceRepository, "save_source")
    assert hasattr(EvidenceRepository, "save_span")
    assert hasattr(EvidenceRepository, "list_sources")


def test_trace_repository_save_load() -> None:
    assert hasattr(TraceRepository, "save_trace")

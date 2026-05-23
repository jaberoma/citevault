"""Ensure fake adapters satisfy domain Protocols."""

from citevault.domain.ports import (
    EmbeddingPort, EvidenceRepository, LLMPort, RerankerPort, RetrievalPort,
    TraceRepository,
)
from tests.fakes import (
    FakeEmbedding, FakeEvidenceRepository, FakeLLM, FakeReranker, FakeRetrieval,
    FakeTraceRepository,
)


def test_fake_llm_satisfies_port() -> None:
    assert isinstance(FakeLLM(), LLMPort)


def test_fake_embedding_satisfies_port() -> None:
    assert isinstance(FakeEmbedding(), EmbeddingPort)


def test_fake_reranker_satisfies_port() -> None:
    assert isinstance(FakeReranker(), RerankerPort)


def test_fake_retrieval_satisfies_port() -> None:
    assert isinstance(FakeRetrieval(), RetrievalPort)


def test_fake_evidence_repository_satisfies_port() -> None:
    assert isinstance(FakeEvidenceRepository(), EvidenceRepository)


def test_fake_trace_repository_satisfies_port() -> None:
    assert isinstance(FakeTraceRepository(), TraceRepository)

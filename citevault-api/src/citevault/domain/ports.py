"""Citevault domain ports (Protocols)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from citevault.domain.models import (
    Achievement, Job, Project, RetrievalCandidate, Skill, Source, Span,
)


@runtime_checkable
class LLMPort(Protocol):
    def complete(
        self, prompt: str, schema: dict[str, Any] | None = None,
        temperature: float = 0.2, system: str | None = None,
    ) -> str: ...


@runtime_checkable
class EmbeddingPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@runtime_checkable
class RerankerPort(Protocol):
    def rerank(
        self, query: str, candidates: list[RetrievalCandidate], top_n: int,
    ) -> list[RetrievalCandidate]: ...


@runtime_checkable
class RetrievalPort(Protocol):
    def hybrid_search(self, query: str, k: int) -> list[RetrievalCandidate]: ...


@runtime_checkable
class EvidenceRepository(Protocol):
    def save_source(self, source: Source) -> None: ...
    def save_span(self, span: Span, embedding: list[float]) -> None: ...
    def save_structured_entry(
        self, entry: Job | Project | Skill | Achievement,
    ) -> None: ...
    def list_sources(self) -> list[Source]: ...
    def get_span(self, span_id: str) -> Span | None: ...
    def list_structured_entries(
        self, source_id: str,
    ) -> list[Job | Project | Skill | Achievement]: ...
    def delete_source(self, source_id: str) -> None: ...
    def list_spans_for_source(self, source_id: str) -> list[Span]: ...


@runtime_checkable
class TraceRepository(Protocol):
    def save_trace(self, trace_json: str, tailoring_id: str) -> None: ...
    def load_trace(self, tailoring_id: str) -> str | None: ...

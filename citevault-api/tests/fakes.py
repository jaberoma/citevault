"""Fake adapters for unit testing domain services."""

from __future__ import annotations

from typing import Any

from citevault.domain.models import Achievement, Job, Project, RetrievalCandidate, Skill, Source, Span


class FakeLLM:
    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = list(responses or [])
        self.calls: list[dict[str, Any]] = []

    def complete(
        self, prompt: str, schema: dict[str, Any] | None = None,
        temperature: float = 0.2, system: str | None = None,
        num_ctx: int | None = None,
    ) -> str:
        self.calls.append({"prompt": prompt, "schema": schema, "temperature": temperature, "system": system, "num_ctx": num_ctx})
        if not self.responses:
            return "(no scripted response)"
        return self.responses.pop(0)


class FakeEmbedding:
    def __init__(self, dim: int = 384) -> None:
        self.dim = dim
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(i + 1) / 1000.0] * self.dim for i, _ in enumerate(texts)]


class FakeReranker:
    def rerank(
        self, query: str, candidates: list[RetrievalCandidate], top_n: int,
    ) -> list[RetrievalCandidate]:
        return list(candidates)[:top_n]


class FakeRetrieval:
    def __init__(self, results: list[RetrievalCandidate] | None = None) -> None:
        self.results = list(results or [])

    def hybrid_search(self, query: str, k: int) -> list[RetrievalCandidate]:
        return self.results[:k]


class FakeEvidenceRepository:
    def __init__(self) -> None:
        self.sources: list[Source] = []
        self.spans: list[tuple[Span, list[float]]] = []
        self.structured_entries: list[Job | Project | Skill | Achievement] = []

    def save_source(self, source: Source) -> None:
        self.sources.append(source)

    def save_span(self, span: Span, embedding: list[float]) -> None:
        self.spans.append((span, embedding))

    def save_structured_entry(self, entry: Job | Project | Skill | Achievement) -> None:
        self.structured_entries.append(entry)

    def list_sources(self) -> list[Source]:
        return list(self.sources)

    def get_span(self, span_id: str) -> Span | None:
        for span, _ in self.spans:
            if span.id == span_id:
                return span
        return None

    def delete_source(self, source_id: str) -> None:
        self.sources = [s for s in self.sources if s.id != source_id]
        self.spans = [(sp, emb) for sp, emb in self.spans if sp.source_id != source_id]

    def list_spans_for_source(self, source_id: str) -> list[Span]:
        return [sp for sp, _ in self.spans if sp.source_id == source_id]

    def list_structured_entries(
        self, source_id: str,
    ) -> list[Job | Project | Skill | Achievement]:
        return [e for e in self.structured_entries if e.source_id == source_id]


class FakeTraceRepository:
    def __init__(self) -> None:
        self.traces: dict[str, str] = {}

    def save_trace(self, trace_json: str, tailoring_id: str) -> None:
        self.traces[tailoring_id] = trace_json

    def load_trace(self, tailoring_id: str) -> str | None:
        return self.traces.get(tailoring_id)

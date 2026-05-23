"""IndexEvidence use case: scans a folder, chunks, embeds, persists."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from citevault.domain.models import Source, SourceKind, Span
from citevault.domain.ports import EmbeddingPort, EvidenceRepository
from citevault.domain.services.chunker import chunk_text
from citevault.domain.services.resume_parser import parse_master_resume

logger = logging.getLogger(__name__)

_SUPPORTED_EXTS = {".md", ".txt", ".pdf"}


@dataclass(frozen=True)
class IndexReport:
    sources_indexed: int
    spans_indexed: int
    structured_entries_indexed: int


def _infer_kind(path: Path) -> SourceKind:
    name = path.stem.lower()
    if "master_resume" in name or name == "resume":
        return SourceKind.RESUME_MASTER
    if name == "readme":
        return SourceKind.README
    return SourceKind.NOTE


def _read_text(path: Path) -> str:
    if path.suffix == ".pdf":
        from pypdf import PdfReader  # optional dependency
        return "\n\n".join(p.extract_text() or "" for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8")


class IndexEvidence:
    def __init__(self, repo: EvidenceRepository, embedder: EmbeddingPort) -> None:
        self._repo = repo
        self._embed = embedder

    def run(self, folder: str) -> IndexReport:
        root = Path(folder)
        sources = 0
        spans = 0
        entries = 0
        logger.info("Indexing evidence from: %s", folder)
        for file in sorted(root.iterdir()):
            if not file.is_file() or file.suffix.lower() not in _SUPPORTED_EXTS:
                continue
            text = _read_text(file)
            kind = _infer_kind(file)
            source = Source(
                id=f"src-{uuid.uuid4().hex[:8]}",
                kind=kind,
                path=file.name,
                text=text,
                created_at=datetime.now(tz=timezone.utc),
            )
            self._repo.save_source(source)
            sources += 1

            chunk_spans = chunk_text(text, max_tokens=512, overlap=50)
            if chunk_spans:
                vectors = self._embed.embed([c.text for c in chunk_spans])
                for c, vec in zip(chunk_spans, vectors):
                    span = Span(
                        id=f"sp-{uuid.uuid4().hex[:8]}",
                        source_id=source.id,
                        start_offset=c.start_offset,
                        end_offset=c.end_offset,
                        text=c.text,
                    )
                    self._repo.save_span(span, embedding=vec)
                    spans += 1

            if source.kind == SourceKind.RESUME_MASTER:
                for entry in parse_master_resume(text, source.id):
                    self._repo.save_structured_entry(entry)
                    entries += 1

            logger.info(
                "Indexed %s (%s) → %d spans%s",
                file.name, kind.value, len(chunk_spans),
                f", {entries} structured entries" if kind == SourceKind.RESUME_MASTER else "",
            )

        logger.info(
            "Indexing complete — %d source(s), %d span(s), %d structured entries",
            sources, spans, entries,
        )
        return IndexReport(
            sources_indexed=sources,
            spans_indexed=spans,
            structured_entries_indexed=entries,
        )

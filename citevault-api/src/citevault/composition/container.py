"""Composition root. Single place where adapters are instantiated and wired."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

from citevault.adapters.outbound.ollama_llm import OllamaLLM
from citevault.adapters.outbound.sqlite_repo import SqliteEvidenceRepository, SqliteTraceRepository

logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    db_path: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:e4b"
    ollama_timeout_s: float = 600.0


class Container:
    """Wires all adapters together. Heavy ML models load in a background thread.

    Check `is_ready` before accessing `embedder`, `reranker`, `retrieval`,
    or `tailor_resume` — they are not set until the background thread finishes.
    """

    llm: OllamaLLM
    evidence_repo: SqliteEvidenceRepository
    trace_repo: SqliteTraceRepository
    # Set by background thread:
    embedder: object
    reranker: object
    retrieval: object
    tailor_resume: object

    def __init__(self, cfg: ContainerConfig) -> None:
        self._ready = threading.Event()
        self._db_path = cfg.db_path
        self.llm = OllamaLLM(base_url=cfg.ollama_base_url, model=cfg.ollama_model, timeout_s=cfg.ollama_timeout_s)
        self.evidence_repo = SqliteEvidenceRepository(cfg.db_path)
        self.trace_repo = SqliteTraceRepository(cfg.db_path)
        threading.Thread(target=self._load_models, daemon=True, name="model-loader").start()

    def _load_models(self) -> None:
        from citevault.adapters.outbound.bge_reranker import BgeReranker
        from citevault.adapters.outbound.sqlite_retrieval import SqliteRetrieval
        from citevault.adapters.outbound.st_embedding import SentenceTransformersEmbedding
        from citevault.application.tailor_resume import TailorResume

        logger.info("Loading ML models in background…")
        self.embedder = SentenceTransformersEmbedding()
        self.reranker = BgeReranker()
        self.retrieval = SqliteRetrieval(db_path=self._db_path, embedder=self.embedder)
        self.tailor_resume = TailorResume(
            retrieval=self.retrieval,
            reranker=self.reranker,
            llm=self.llm,
            span_lookup=self.evidence_repo,
            trace_repo=self.trace_repo,
        )
        self._ready.set()
        logger.info("ML models ready.")

    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()

    def wait_ready(self, timeout: float | None = None) -> bool:
        """Block until models are loaded. Returns True if ready, False on timeout."""
        return self._ready.wait(timeout=timeout)

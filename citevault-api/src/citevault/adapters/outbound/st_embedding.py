"""sentence-transformers BGE-small embedding adapter."""

from __future__ import annotations

import logging
import time

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SentenceTransformersEmbedding:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        logger.info("Embedding model ready: %s", model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        t0 = time.monotonic()
        result = [list(map(float, vec)) for vec in self._model.encode(texts)]
        logger.debug("Embedded %d texts in %.2fs", len(texts), time.monotonic() - t0)
        return result

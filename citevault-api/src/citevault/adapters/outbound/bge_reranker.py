"""BGE re-ranker (cross-encoder) adapter."""

from __future__ import annotations

import logging
import time

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from citevault.domain.models import RetrievalCandidate

logger = logging.getLogger(__name__)


class BgeReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading reranker model: %s (device=%s)", model_name, self._device)
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self._model.to(self._device)
        self._model.eval()
        logger.info("Reranker model ready: %s", model_name)

    def rerank(
        self, query: str, candidates: list[RetrievalCandidate], top_n: int,
    ) -> list[RetrievalCandidate]:
        if not candidates:
            return []
        t0 = time.monotonic()

        queries = [query] * len(candidates)
        texts = [c.text for c in candidates]
        inputs = self._tokenizer(
            queries, texts,
            truncation=True, max_length=512, padding=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)

        if outputs.logits.shape[-1] == 1:
            raw_scores = outputs.logits.squeeze(-1).tolist()
        else:
            raw_scores = outputs.logits[:, 1].tolist()

        scored = sorted(zip(candidates, raw_scores), key=lambda x: x[1], reverse=True)
        result = [c.model_copy(update={"score": float(s)}) for c, s in scored[:top_n]]
        logger.debug(
            "Reranked %d → top %d in %.2fs", len(candidates), len(result),
            time.monotonic() - t0,
        )
        return result

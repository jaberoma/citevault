"""BGE-small embedding adapter tests (uses real model — runs once and caches)."""

import pytest

from citevault.adapters.outbound.st_embedding import SentenceTransformersEmbedding


@pytest.fixture(scope="module")
def embedder() -> SentenceTransformersEmbedding:
    return SentenceTransformersEmbedding()


def test_embed_returns_correct_dimension(embedder: SentenceTransformersEmbedding) -> None:
    vectors = embedder.embed(["hello world"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 384  # BGE-small-en-v1.5 dim


def test_embed_two_texts(embedder: SentenceTransformersEmbedding) -> None:
    vectors = embedder.embed(["one", "two"])
    assert len(vectors) == 2
    assert vectors[0] != vectors[1]

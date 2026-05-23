"""BGE re-ranker adapter tests."""

import pytest

from citevault.adapters.outbound.bge_reranker import BgeReranker
from citevault.domain.models import RetrievalCandidate


@pytest.fixture(scope="module")
def reranker() -> BgeReranker:
    return BgeReranker()


def test_rerank_promotes_relevant_candidate(reranker: BgeReranker) -> None:
    cands = [
        RetrievalCandidate(span_id="a", text="The cat sat on the mat.", score=0.5),
        RetrievalCandidate(span_id="b", text="Kubernetes is a container orchestrator.",
                           score=0.5),
        RetrievalCandidate(span_id="c", text="I had pasta for dinner.", score=0.5),
    ]
    ranked = reranker.rerank("k8s orchestration", cands, top_n=3)
    assert ranked[0].span_id == "b"


def test_rerank_top_n_limits(reranker: BgeReranker) -> None:
    cands = [
        RetrievalCandidate(span_id=f"s{i}", text=f"text {i}", score=0.5)
        for i in range(10)
    ]
    ranked = reranker.rerank("query", cands, top_n=3)
    assert len(ranked) == 3


def test_rerank_all_scores_updated_from_model(reranker: BgeReranker) -> None:
    """Every returned candidate must carry the model's score, not the input score."""
    cands = [
        RetrievalCandidate(span_id="a", text="Kubernetes container orchestration.", score=0.5),
        RetrievalCandidate(span_id="b", text="Python is a programming language.", score=0.5),
        RetrievalCandidate(span_id="c", text="Deploy microservices with k8s.", score=0.5),
    ]
    ranked = reranker.rerank("k8s deployment", cands, top_n=3)
    scores = [c.score for c in ranked]
    assert all(s != 0.5 for s in scores), "scores should come from the model, not input defaults"
    assert scores == sorted(scores, reverse=True), "candidates must be in descending score order"

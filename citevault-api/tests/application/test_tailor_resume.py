"""End-to-end tailoring with fakes — no real LLM/embedding involvement."""

import json

from citevault.application.tailor_resume import TailorResume
from citevault.domain.models import (
    ClaimStatus, JobPosting, Requirement, RequirementKind, RetrievalCandidate,
    Span,
)
from tests.fakes import FakeLLM, FakeReranker, FakeRetrieval, FakeTraceRepository


class StubSpanLookup:
    def __init__(self) -> None:
        self.spans = {
            "sp1": Span(id="sp1", source_id="s1", start_offset=0, end_offset=10,
                        text="Built K8s"),
        }

    def get_span(self, span_id: str) -> Span | None:
        return self.spans.get(span_id)


def test_tailoring_produces_verified_and_rejected_claims() -> None:
    jp = JobPosting(
        id="jp1", raw_text="...",
        role_title="Senior Backend Engineer", company="TechCo",
        requirements=[
            Requirement(id="r1", text="K8s",
                        kind=RequirementKind.MUST_HAVE, priority=1),
            Requirement(id="r2", text="Rust",
                        kind=RequirementKind.NICE_TO_HAVE, priority=5),
        ],
    )
    drafter_resp = json.dumps({"claims": [
        {"text": "Built K8s", "claim_type": "achievement", "citations": ["sp1"]},
    ]})
    verifier_resp = json.dumps({
        "verdict": "SUPPORTS", "confidence": 0.9, "explanation": "ok",
    })

    use_case = TailorResume(
        retrieval=_RetrievalByQuery({
            "K8s": [RetrievalCandidate(span_id="sp1", text="Built K8s", score=0.9)],
            "Rust": [],
        }),
        reranker=FakeReranker(),
        llm=FakeLLM(responses=[drafter_resp, verifier_resp]),
        span_lookup=StubSpanLookup(),
        trace_repo=FakeTraceRepository(),
    )

    result = use_case.run(jp, tailoring_id="t1")
    statuses = [c.status for c in result.verified_claims]
    assert ClaimStatus.VERIFIED in statuses
    assert len(result.gap_report.entries) == 1
    assert "Rust" in result.gap_report.entries[0].requirement_text


def test_trace_is_valid_json_with_nested_objects() -> None:
    """Trace must round-trip through JSON with nested dicts, not str() reprs."""
    jp = JobPosting(
        id="jp1", raw_text="...",
        role_title="Senior Backend Engineer", company="TechCo",
        requirements=[
            Requirement(id="r1", text="K8s",
                        kind=RequirementKind.MUST_HAVE, priority=1),
        ],
    )
    drafter_resp = json.dumps({"claims": [
        {"text": "Built K8s", "claim_type": "achievement", "citations": ["sp1"]},
    ]})
    verifier_resp = json.dumps({
        "verdict": "SUPPORTS", "confidence": 0.9, "explanation": "ok",
    })
    trace_repo = FakeTraceRepository()
    use_case = TailorResume(
        retrieval=_RetrievalByQuery({
            "K8s": [RetrievalCandidate(span_id="sp1", text="Built K8s", score=0.9)],
        }),
        reranker=FakeReranker(),
        llm=FakeLLM(responses=[drafter_resp, verifier_resp]),
        span_lookup=StubSpanLookup(),
        trace_repo=trace_repo,
    )
    use_case.run(jp, tailoring_id="t2")

    raw = trace_repo.load_trace("t2")
    assert raw is not None
    parsed = json.loads(raw)
    assert isinstance(parsed["job_posting"], dict), (
        "job_posting must be a dict, not a string repr of a Pydantic model"
    )
    assert isinstance(parsed["gap_report"], dict)
    assert isinstance(parsed["verified_claims"], list)
    if parsed["verified_claims"]:
        assert isinstance(parsed["verified_claims"][0], dict)


def test_tailoring_result_includes_summary() -> None:
    jp = JobPosting(
        id="jp1", raw_text="...",
        role_title="Sr Engineer", company="Co",
        requirements=[
            Requirement(id="r1", text="K8s", kind=RequirementKind.MUST_HAVE, priority=1),
        ],
    )
    drafter_resp = json.dumps({"claims": [
        {"text": "I did K8s", "claim_type": "achievement", "citations": ["sp1"]},
    ]})
    verifier_resp = json.dumps({"verdict": "SUPPORTS", "confidence": 0.9, "explanation": "ok"})
    use_case = TailorResume(
        retrieval=_RetrievalByQuery({
            "K8s": [RetrievalCandidate(span_id="sp1", text="I did K8s", score=0.9)],
        }),
        reranker=FakeReranker(),
        llm=FakeLLM(responses=[drafter_resp, verifier_resp]),
        span_lookup=StubSpanLookup(),
        trace_repo=FakeTraceRepository(),
    )
    result = use_case.run(jp, tailoring_id="t3")
    assert result.summary.drafts_total == 1
    assert result.summary.first_pass_verified == 1
    assert result.summary.requirements_total == 1
    assert result.summary.requirements_met == 1


class _RetrievalByQuery:
    def __init__(self, mapping: dict[str, list[RetrievalCandidate]]) -> None:
        self._m = mapping
    def hybrid_search(self, query: str, k: int) -> list[RetrievalCandidate]:
        for key, val in self._m.items():
            if key.lower() in query.lower():
                return val
        return []


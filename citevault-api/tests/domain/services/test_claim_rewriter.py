"""ClaimRewriter applies the refuse-or-rewrite policy."""

import json

from citevault.domain.models import (
    Citation, Claim, ClaimStatus, ClaimType, Span, VerdictKind, VerificationResult,
)
from citevault.domain.services.claim_rewriter import ClaimRewriter, ClaimOutcome
from tests.fakes import FakeLLM


def _claim() -> Claim:
    return Claim(id="c1", text="Built scalable K8s in production",
                 claim_type=ClaimType.ACHIEVEMENT,
                 citations=[Citation(span_id="sp1")],
                 status=ClaimStatus.DRAFT)


def _span() -> Span:
    return Span(id="sp1", source_id="src1", start_offset=0,
                end_offset=30, text="Built KuberDocs for K8s.")


def _vr(verdict: VerdictKind) -> VerificationResult:
    return VerificationResult(claim_id="c1", verdict=verdict, confidence=0.7,
                              explanation="...")


def test_supports_kept_as_verified() -> None:
    rewriter = ClaimRewriter(llm=FakeLLM(),
                              verifier=lambda c, s: _vr(VerdictKind.SUPPORTS))
    outcome = rewriter.process(_claim(), [_span()])
    assert outcome.final_status == ClaimStatus.VERIFIED
    assert outcome.claim.text == "Built scalable K8s in production"


def test_contradicts_rejected() -> None:
    rewriter = ClaimRewriter(llm=FakeLLM(),
                              verifier=lambda c, s: _vr(VerdictKind.CONTRADICTS))
    outcome = rewriter.process(_claim(), [_span()])
    assert outcome.final_status == ClaimStatus.REJECTED


def test_partial_then_rewrite_then_supports() -> None:
    verdicts = iter([VerdictKind.PARTIAL, VerdictKind.SUPPORTS])
    rewriter = ClaimRewriter(
        llm=FakeLLM(responses=["Built KuberDocs for K8s."]),
        verifier=lambda c, s: _vr(next(verdicts)),
    )
    outcome = rewriter.process(_claim(), [_span()])
    assert outcome.final_status == ClaimStatus.REWRITTEN
    assert outcome.claim.text == "Built KuberDocs for K8s."


def test_two_failed_rewrites_rejects() -> None:
    rewriter = ClaimRewriter(
        llm=FakeLLM(responses=["attempt 1", "attempt 2"]),
        verifier=lambda c, s: _vr(VerdictKind.UNCLEAR),  # never improves
    )
    outcome = rewriter.process(_claim(), [_span()])
    assert outcome.final_status == ClaimStatus.REJECTED
    assert outcome.rewrite_attempts == 2


def test_empty_rewrite_text_is_rejected() -> None:
    """When LLM returns empty string as rewrite, the claim must be rejected immediately."""
    verdicts = iter([VerdictKind.PARTIAL])
    rewriter = ClaimRewriter(
        llm=FakeLLM(responses=[""]),
        verifier=lambda c, s: _vr(next(verdicts)),
    )
    outcome = rewriter.process(_claim(), [_span()])
    assert outcome.final_status == ClaimStatus.REJECTED
    assert "empty" in outcome.last_explanation.lower()


def test_rewriter_passes_system_prompt_to_llm() -> None:
    verdicts = iter([VerdictKind.PARTIAL, VerdictKind.SUPPORTS])
    llm = FakeLLM(responses=["Rewritten claim."])
    rewriter = ClaimRewriter(llm=llm, verifier=lambda c, s: _vr(next(verdicts)))
    rewriter.process(_claim(), [_span()])
    assert llm.calls[0].get("system") is not None

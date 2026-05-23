"""Stage B verifier tests using fakes."""

import json

from citevault.domain.models import (
    Citation, Claim, ClaimStatus, ClaimType, Span, VerdictKind,
)
from citevault.domain.services.grounding_verifier import GroundingVerifier
from tests.fakes import FakeLLM


def _claim() -> Claim:
    return Claim(
        id="c1", text="Led K8s migration",
        claim_type=ClaimType.ACHIEVEMENT,
        citations=[Citation(span_id="sp1")],
        status=ClaimStatus.DRAFT,
    )


def _span() -> Span:
    return Span(id="sp1", source_id="src1", start_offset=0,
                end_offset=20, text="Migrated to Kubernetes.")


def test_verifier_returns_supports_verdict() -> None:
    scripted = json.dumps({
        "verdict": "SUPPORTS", "confidence": 0.95,
        "explanation": "Evidence supports the claim.",
    })
    v = GroundingVerifier(llm=FakeLLM(responses=[scripted]))
    result = v.verify(_claim(), [_span()])
    assert result.verdict == VerdictKind.SUPPORTS
    assert result.confidence == 0.95


def test_verifier_returns_partial_verdict() -> None:
    scripted = json.dumps({
        "verdict": "PARTIAL", "confidence": 0.6,
        "explanation": "Evidence supports part, but overstates scope.",
    })
    v = GroundingVerifier(llm=FakeLLM(responses=[scripted]))
    result = v.verify(_claim(), [_span()])
    assert result.verdict == VerdictKind.PARTIAL


def test_verifier_uses_low_temperature() -> None:
    fake = FakeLLM(responses=[json.dumps(
        {"verdict": "UNCLEAR", "confidence": 0.3, "explanation": "x"})])
    GroundingVerifier(llm=fake).verify(_claim(), [_span()])
    assert fake.calls[0]["temperature"] <= 0.1


def test_verifier_returns_contradicts_verdict() -> None:
    scripted = json.dumps({
        "verdict": "CONTRADICTS", "confidence": 0.85,
        "explanation": "Evidence says the opposite.",
    })
    v = GroundingVerifier(llm=FakeLLM(responses=[scripted]))
    result = v.verify(_claim(), [_span()])
    assert result.verdict == VerdictKind.CONTRADICTS


def test_verifier_raises_on_malformed_json() -> None:
    v = GroundingVerifier(llm=FakeLLM(responses=["not json {"]))
    try:
        v.verify(_claim(), [_span()])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "malformed JSON" in str(exc)


def test_verifier_raises_on_unknown_verdict() -> None:
    scripted = json.dumps(
        {"verdict": "UNSUPPORTED", "confidence": 0.5, "explanation": "x"})
    v = GroundingVerifier(llm=FakeLLM(responses=[scripted]))
    try:
        v.verify(_claim(), [_span()])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unexpected verification payload" in str(exc)


def test_verifier_clamps_out_of_range_confidence() -> None:
    scripted = json.dumps(
        {"verdict": "SUPPORTS", "confidence": 1.5, "explanation": "x"})
    v = GroundingVerifier(llm=FakeLLM(responses=[scripted]))
    result = v.verify(_claim(), [_span()])
    assert result.confidence == 1.0


def test_verifier_empty_spans_uses_none_placeholder() -> None:
    scripted = json.dumps(
        {"verdict": "UNCLEAR", "confidence": 0.2, "explanation": "no evidence"})
    fake = FakeLLM(responses=[scripted])
    GroundingVerifier(llm=fake).verify(_claim(), [])
    assert "(none)" in fake.calls[0]["prompt"]


def test_verifier_passes_system_prompt_to_llm() -> None:
    scripted = json.dumps({"verdict": "SUPPORTS", "confidence": 0.9, "explanation": "ok"})
    fake = FakeLLM(responses=[scripted])
    GroundingVerifier(llm=fake).verify(_claim(), [_span()])
    assert fake.calls[0].get("system") is not None

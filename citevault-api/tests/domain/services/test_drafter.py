"""Stage A drafter tests using fakes."""

import json

from citevault.domain.models import (
    ClaimType, RetrievalCandidate, Requirement, RequirementKind,
)
from citevault.domain.services.drafter import StageADrafter
from tests.fakes import FakeLLM


def test_drafter_produces_claims_with_citations() -> None:
    scripted = json.dumps({
        "claims": [
            {"text": "Led migration of payment service to Kubernetes",
             "claim_type": "achievement", "citations": ["sp-1"]},
        ]
    })
    drafter = StageADrafter(llm=FakeLLM(responses=[scripted]))
    req = Requirement(id="r-1", text="K8s in production",
                      kind=RequirementKind.MUST_HAVE, priority=1)
    candidates = [RetrievalCandidate(span_id="sp-1",
                                      text="Built KuberDocs for k8s.", score=0.9)]
    claims = drafter.draft(req, candidates)
    assert len(claims) == 1
    assert claims[0].claim_type == ClaimType.ACHIEVEMENT
    assert claims[0].citations[0].span_id == "sp-1"


def test_drafter_rejects_claims_citing_unknown_spans() -> None:
    scripted = json.dumps({
        "claims": [
            {"text": "Hallucinated claim", "claim_type": "skill",
             "citations": ["sp-999"]},   # not in retrieved set
        ]
    })
    drafter = StageADrafter(llm=FakeLLM(responses=[scripted]))
    req = Requirement(id="r-2", text="Anything",
                      kind=RequirementKind.NICE_TO_HAVE, priority=5)
    claims = drafter.draft(req, [RetrievalCandidate(span_id="sp-1",
                                                     text="X", score=0.5)])
    assert claims == []


def test_drafter_raises_on_malformed_json() -> None:
    drafter = StageADrafter(llm=FakeLLM(responses=["not json {"]))
    req = Requirement(id="r-3", text="Anything",
                      kind=RequirementKind.MUST_HAVE, priority=1)
    try:
        drafter.draft(req, [RetrievalCandidate(span_id="sp-1", text="X", score=0.5)])
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "malformed JSON" in str(exc)


def test_drafter_passes_system_prompt_to_llm() -> None:
    scripted = json.dumps({"claims": []})
    llm = FakeLLM(responses=[scripted])
    req = Requirement(id="r-5", text="K8s", kind=RequirementKind.MUST_HAVE, priority=1)
    StageADrafter(llm=llm).draft(req, [])
    assert llm.calls[0].get("system") is not None


def test_drafter_skips_claims_with_unknown_claim_type() -> None:
    scripted = json.dumps({
        "claims": [
            {"text": "Valid claim", "claim_type": "achievement", "citations": ["sp-1"]},
            {"text": "Bad type", "claim_type": "INVENTED_TYPE", "citations": ["sp-1"]},
        ]
    })
    drafter = StageADrafter(llm=FakeLLM(responses=[scripted]))
    req = Requirement(id="r-4", text="K8s",
                      kind=RequirementKind.MUST_HAVE, priority=1)
    claims = drafter.draft(req, [RetrievalCandidate(span_id="sp-1",
                                                     text="K8s stuff", score=0.9)])
    assert len(claims) == 1
    assert claims[0].text == "Valid claim"

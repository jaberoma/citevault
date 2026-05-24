"""Cover-letter generation with grounded sentences."""

import json

from citevault.domain.models import (
    Citation, Claim, ClaimStatus, ClaimType, JobPosting,
)
from citevault.domain.services.cover_letter import CoverLetterComposer
from tests.fakes import FakeLLM


def test_compose_returns_cover_letter_markdown() -> None:
    jp = JobPosting(id="jp1", raw_text="Senior Backend role at TechCo",
                    role_title="Senior Backend Engineer", company="TechCo",
                    requirements=[])
    claims = [
        Claim(id="c1", text="Built K8s tooling",
              claim_type=ClaimType.ACHIEVEMENT,
              citations=[Citation(span_id="sp1")],
              status=ClaimStatus.VERIFIED),
    ]
    scripted = json.dumps({"paragraphs": [
        "I am writing to apply for the Senior Backend Engineer role at TechCo.",
        "I bring relevant experience: I built K8s tooling.",
        "I would welcome the opportunity to discuss further.",
    ]})
    composer = CoverLetterComposer(llm=FakeLLM(responses=[scripted]))
    md = composer.compose(jp, claims)
    assert "Senior Backend Engineer" in md
    assert "TechCo" in md
    assert "K8s" in md


def test_cover_letter_passes_system_prompt_to_llm() -> None:
    jp = JobPosting(id="jp1", raw_text="Role", role_title="Engineer", requirements=[])
    scripted = json.dumps({"paragraphs": ["Dear Hiring Manager."]})
    llm = FakeLLM(responses=[scripted])
    CoverLetterComposer(llm=llm).compose(jp, [])
    assert llm.calls[0].get("system") is not None

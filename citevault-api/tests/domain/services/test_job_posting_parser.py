"""JobPostingParser uses LLM (faked) to extract requirements."""

import json

from citevault.domain.models import RequirementKind
from citevault.domain.services.job_posting_parser import JobPostingParser
from tests.fakes import FakeLLM


def test_parser_returns_structured_requirements() -> None:
    scripted = json.dumps({
        "role_title": "Senior Backend Engineer",
        "company": "TechCo",
        "requirements": [
            {"text": "5+ years distributed systems",
             "kind": "must_have", "priority": 1},
            {"text": "Rust", "kind": "nice_to_have", "priority": 5},
        ],
    })
    parser = JobPostingParser(llm=FakeLLM(responses=[scripted]))
    jp = parser.parse(posting_text="We're looking for a Senior Backend Engineer at TechCo...")
    assert jp.role_title == "Senior Backend Engineer"
    assert jp.company == "TechCo"
    assert len(jp.requirements) == 2
    assert jp.requirements[0].kind == RequirementKind.MUST_HAVE
    assert jp.requirements[1].kind == RequirementKind.NICE_TO_HAVE


def test_parser_raises_value_error_on_malformed_json() -> None:
    parser = JobPostingParser(llm=FakeLLM(responses=["not valid json {"]))
    try:
        parser.parse(posting_text="Some job posting text.")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "malformed JSON" in str(exc)


def test_parser_passes_system_prompt_to_llm() -> None:
    scripted = json.dumps({"role_title": "Dev", "company": "Co", "requirements": []})
    llm = FakeLLM(responses=[scripted])
    JobPostingParser(llm=llm).parse("Any posting.")
    assert llm.calls[0].get("system") is not None


def test_parser_skips_requirements_with_missing_fields() -> None:
    scripted = json.dumps({
        "role_title": "Dev",
        "company": "Co",
        "requirements": [
            {"text": "Good field", "kind": "must_have", "priority": 1},
            {"kind": "nice_to_have", "priority": 2},  # missing "text"
        ],
    })
    parser = JobPostingParser(llm=FakeLLM(responses=[scripted]))
    jp = parser.parse(posting_text="Job posting.")
    assert len(jp.requirements) == 1
    assert jp.requirements[0].text == "Good field"

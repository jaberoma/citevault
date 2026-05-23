"""Domain model tests."""

from datetime import datetime

from citevault.domain.models import Source, SourceKind, Span


def test_source_construction() -> None:
    src = Source(
        id="src-1",
        kind=SourceKind.RESUME_MASTER,
        path="master_resume.md",
        text="Senior Backend Engineer at TechCorp.",
        created_at=datetime(2026, 5, 11, 10, 0, 0),
    )
    assert src.id == "src-1"
    assert src.kind == SourceKind.RESUME_MASTER
    assert "TechCorp" in src.text


def test_span_extracts_correct_substring() -> None:
    text = "Hello world, goodbye world."
    span = Span(id="sp-1", source_id="src-1", start_offset=6, end_offset=11, text="world")
    assert span.text == text[span.start_offset : span.end_offset]


def test_job_with_bullets_and_evidence_spans() -> None:
    from citevault.domain.models import Job

    job = Job(
        id="job-1",
        source_id="src-1",
        company="TechCorp",
        role="Senior Backend Engineer",
        start_date="2021-01",
        end_date=None,
        bullets=["Led migration of payment service.", "Mentored 2 junior engineers."],
        evidence_span_ids=["sp-3", "sp-4"],
    )
    assert job.end_date is None
    assert len(job.bullets) == 2
    assert "sp-3" in job.evidence_span_ids


def test_project_skill_achievement() -> None:
    from citevault.domain.models import Achievement, Project, Skill

    p = Project(
        id="p-1",
        source_id="src-2",
        name="KuberDocs",
        role="author",
        technologies=["Go", "Helm"],
        bullets=["OSS tool for K8s docs."],
        evidence_span_ids=["sp-9"],
    )
    s = Skill(id="sk-1", source_id="src-1", name="Java", evidence_span_ids=["sp-2"])
    a = Achievement(
        id="ach-1",
        source_id="src-1",
        description="Cut API latency 40%.",
        evidence_span_ids=["sp-5"],
    )
    assert "Go" in p.technologies
    assert s.name == "Java"
    assert "40%" in a.description


def test_requirement_kinds() -> None:
    from citevault.domain.models import Requirement, RequirementKind

    r = Requirement(
        id="r-1", text="5+ years distributed systems",
        kind=RequirementKind.MUST_HAVE, priority=1,
    )
    assert r.kind == RequirementKind.MUST_HAVE


def test_claim_with_citations() -> None:
    from citevault.domain.models import Claim, Citation, ClaimStatus, ClaimType

    c = Claim(
        id="c-1",
        text="Led K8s migration",
        claim_type=ClaimType.ACHIEVEMENT,
        citations=[Citation(span_id="sp-1"), Citation(structured_entry_id="job-1")],
        status=ClaimStatus.VERIFIED,
    )
    assert c.status == ClaimStatus.VERIFIED
    assert len(c.citations) == 2


def test_verification_result_verdicts() -> None:
    from citevault.domain.models import VerificationResult, VerdictKind

    v = VerificationResult(
        claim_id="c-1", verdict=VerdictKind.PARTIAL,
        confidence=0.6, explanation="Evidence supports part of claim.",
    )
    assert v.verdict == VerdictKind.PARTIAL


def test_job_posting_with_requirements() -> None:
    from citevault.domain.models import JobPosting, Requirement, RequirementKind

    jp = JobPosting(
        id="jp-1",
        raw_text="Senior backend role. 5+ years distributed.",
        role_title="Senior Backend Engineer",
        company=None,
        requirements=[
            Requirement(id="r-1", text="5+ years distributed",
                        kind=RequirementKind.MUST_HAVE, priority=1),
        ],
    )
    assert len(jp.requirements) == 1


def test_gap_report_contains_entries() -> None:
    from citevault.domain.models import GapEntry, GapReport

    gr = GapReport(
        tailoring_id="t-1",
        entries=[GapEntry(
            requirement_text="Rust experience",
            closest_evidence=None,
            neutral_suggestion="Consider flagging as learning interest.",
        )],
    )
    assert "Rust" in gr.entries[0].requirement_text

"""Markdown rendering with citation footnotes."""

from citevault.adapters.outbound.markdown_renderer import (
    render_resume_markdown, render_resume_pdf_html,
)
from citevault.application.tailor_resume import TailoringResult
from citevault.domain.models import (
    Citation, Claim, ClaimStatus, ClaimType, GapReport, Job, JobPosting,
)


def _make_job(**kwargs) -> Job:  # type: ignore[no-untyped-def]
    defaults = dict(
        id="job-1", source_id="src-1",
        company="TechCorp", role="Senior Backend Engineer",
        start_date="2021-01", end_date=None,
        bullets=["Led K8s migration", "Reduced latency 40%"],
    )
    return Job(**(defaults | kwargs))


def test_render_includes_role_company_and_claim_footnote() -> None:
    jp = JobPosting(id="jp1", raw_text="...",
                    role_title="Senior Backend Engineer", company="TechCo",
                    requirements=[])
    claim = Claim(id="c1", text="Led K8s migration",
                  claim_type=ClaimType.ACHIEVEMENT,
                  citations=[Citation(span_id="sp1")],
                  status=ClaimStatus.VERIFIED)
    result = TailoringResult(tailoring_id="t1", job_posting=jp,
                              verified_claims=[claim],
                              gap_report=GapReport(tailoring_id="t1", entries=[]))
    md = render_resume_markdown(result,
                                  span_texts={"sp1": "Migrated to Kubernetes."})
    assert "Senior Backend Engineer" in md
    assert "TechCo" in md
    assert "Led K8s migration" in md
    assert "[^sp1]" in md
    assert "[^sp1]: Migrated to Kubernetes." in md


def _make_result() -> tuple:
    jp = JobPosting(id="jp1", raw_text="...",
                    role_title="Senior Backend Engineer", company="TechCo",
                    requirements=[])
    claim = Claim(id="c1", text="Led K8s migration",
                  claim_type=ClaimType.ACHIEVEMENT,
                  citations=[Citation(span_id="sp1")],
                  status=ClaimStatus.VERIFIED)
    result = TailoringResult(tailoring_id="t1", job_posting=jp,
                              verified_claims=[claim],
                              gap_report=GapReport(tailoring_id="t1", entries=[]))
    span_texts = {"sp1": "Migrated to Kubernetes."}
    return result, span_texts


def test_pdf_html_strips_citation_markers() -> None:
    result, span_texts = _make_result()
    html = render_resume_pdf_html(result, span_texts)
    assert "[^sp1]" not in html
    assert "Led K8s migration" in html


def test_pdf_html_has_sources_appendix() -> None:
    result, span_texts = _make_result()
    html = render_resume_pdf_html(result, span_texts)
    assert "Sources" in html
    assert "Migrated to Kubernetes." in html


def test_pdf_html_sources_on_new_page() -> None:
    result, span_texts = _make_result()
    html = render_resume_pdf_html(result, span_texts)
    assert "page-break-before" in html


def test_render_markdown_includes_experience_section() -> None:
    result, span_texts = _make_result()
    job = _make_job()
    md = render_resume_markdown(result, span_texts, cited_jobs=[job])
    assert "## Experience" in md
    assert "Senior Backend Engineer" in md
    assert "TechCorp" in md
    assert "Led K8s migration" in md
    assert "present" in md


def test_render_markdown_experience_appears_after_highlights() -> None:
    result, span_texts = _make_result()
    md = render_resume_markdown(result, span_texts, cited_jobs=[_make_job()])
    assert md.index("## Highlights") < md.index("## Experience")


def test_render_markdown_experience_sorted_most_recent_first() -> None:
    result, span_texts = _make_result()
    jobs = [
        _make_job(id="j1", role="Junior Engineer", start_date="2018-03", end_date="2021-01"),
        _make_job(id="j2", role="Senior Engineer", start_date="2021-01", end_date=None),
    ]
    md = render_resume_markdown(result, span_texts, cited_jobs=jobs)
    assert md.index("Senior Engineer") < md.index("Junior Engineer")


def test_render_markdown_omits_experience_when_no_jobs() -> None:
    result, span_texts = _make_result()
    md = render_resume_markdown(result, span_texts, cited_jobs=[])
    assert "## Experience" not in md


def test_pdf_html_includes_experience_section() -> None:
    result, span_texts = _make_result()
    html = render_resume_pdf_html(result, span_texts, cited_jobs=[_make_job()])
    assert "Experience" in html
    assert "TechCorp" in html
    assert "Led K8s migration" in html
    assert "present" in html


def test_pdf_html_omits_experience_when_no_jobs() -> None:
    result, span_texts = _make_result()
    html = render_resume_pdf_html(result, span_texts, cited_jobs=[])
    assert "Experience" not in html

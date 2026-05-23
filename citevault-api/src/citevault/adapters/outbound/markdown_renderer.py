"""Render TailoringResult as Markdown with footnoted citations."""

from __future__ import annotations

from citevault.application.tailor_resume import TailoringResult
from citevault.domain.models import Job


def _format_date(ym: str) -> str:
    if not ym or ym == "0000-00":
        return ""
    try:
        year, month = ym.split("-")
        from calendar import month_abbr
        return f"{month_abbr[int(month)]} {year}"
    except (ValueError, IndexError):
        return ym


def _sort_jobs(jobs: list[Job]) -> list[Job]:
    def key(j: Job) -> str:
        return j.end_date or "9999-99"
    return sorted(jobs, key=key, reverse=True)


def render_resume_markdown(
    result: TailoringResult,
    span_texts: dict[str, str],
    cited_jobs: list[Job] | None = None,
) -> str:
    jp = result.job_posting
    lines: list[str] = []
    if jp.role_title:
        lines.append(f"# Tailored for: {jp.role_title}")
    if jp.company:
        lines.append(f"_{jp.company}_")
    lines.append("")
    lines.append("## Highlights")
    used_span_ids: set[str] = set()
    for claim in result.verified_claims:
        ids = [c.span_id for c in claim.citations if c.span_id]
        used_span_ids.update(ids)
        markers = "".join(f"[^{sid}]" for sid in ids)
        lines.append(f"- {claim.text}{markers}")
    lines.append("")
    if cited_jobs:
        lines.append("## Experience")
        for job in _sort_jobs(cited_jobs):
            start = _format_date(job.start_date)
            end = _format_date(job.end_date) if job.end_date else "present"
            date_range = f"{start} – {end}" if start else end
            lines.append(f"### {job.role} · {job.company}")
            lines.append(f"_{date_range}_")
            lines.append("")
            for bullet in job.bullets:
                lines.append(f"- {bullet}")
            lines.append("")

    if used_span_ids:
        lines.append("## Sources")
        for sid in sorted(used_span_ids):
            text = span_texts.get(sid, "(span text unavailable)")
            lines.append(f"[^{sid}]: {text}")
    return "\n".join(lines) + "\n"


def render_resume_pdf_html(
    result: TailoringResult,
    span_texts: dict[str, str],
    cited_jobs: list[Job] | None = None,
) -> str:
    jp = result.job_posting
    parts: list[str] = []

    if jp.role_title:
        parts.append(f"<h1>Tailored for: {jp.role_title}</h1>")
    if jp.company:
        parts.append(f"<p><em>{jp.company}</em></p>")

    parts.append("<h2>Highlights</h2><ul>")
    used_spans: dict[str, str] = {}
    ref_num = 1
    for claim in result.verified_claims:
        ids = [c.span_id for c in claim.citations if c.span_id]
        refs = "".join(f"<sup>[{i}]</sup>" for i in range(ref_num, ref_num + len(ids)))
        for sid in ids:
            used_spans[sid] = str(ref_num)
            ref_num += 1
        parts.append(f"<li>{claim.text}{refs}</li>")
    parts.append("</ul>")

    if cited_jobs:
        parts.append("<h2>Experience</h2>")
        for job in _sort_jobs(cited_jobs):
            start = _format_date(job.start_date)
            end = _format_date(job.end_date) if job.end_date else "present"
            date_range = f"{start} – {end}" if start else end
            parts.append(f"<h3>{job.role} — {job.company}</h3>")
            parts.append(f"<p class='dates'><em>{date_range}</em></p>")
            if job.bullets:
                parts.append("<ul>")
                for bullet in job.bullets:
                    escaped = bullet.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    parts.append(f"<li>{escaped}</li>")
                parts.append("</ul>")

    if used_spans:
        parts.append(
            "<div style='page-break-before: always'>"
            "<h2>Sources</h2><ol>"
        )
        for sid, num in used_spans.items():
            text = span_texts.get(sid, "(unavailable)")
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f"<li value='{num}'><small>{escaped}</small></li>")
        parts.append("</ol></div>")

    return "\n".join(parts)


def render_gaps_markdown(result: TailoringResult) -> str:
    lines = ["# Gap Report", ""]
    if not result.gap_report.entries:
        lines.append("_No gaps. All requirements are grounded._")
        return "\n".join(lines) + "\n"
    for entry in result.gap_report.entries:
        lines.append(f"## {entry.requirement_text}")
        if entry.closest_evidence:
            lines.append(f"**Closest evidence found:** {entry.closest_evidence}")
        lines.append(f"**Suggestion:** {entry.neutral_suggestion}")
        lines.append("")
    return "\n".join(lines) + "\n"

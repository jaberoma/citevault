"""Rule-based master-résumé parser.

Recognizes Markdown sections with conventions:
  # Experience      → following ## items are Jobs
  # Projects        → following ## items are Projects
  # Skills          → comma- or newline-separated list of skill names

Date convention in job/project headers: "Role · Company · YYYY-MM – YYYY-MM"
or "Role · Company · YYYY-MM – present"
"""

from __future__ import annotations

import re
import uuid

from citevault.domain.models import Achievement, Job, Project, Skill

_HEADER_RE = re.compile(r"^#\s+(?P<name>.+?)\s*$", re.M)
_SUB_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$", re.M)
_DATE_RANGE_RE = re.compile(
    r"(?P<start>\d{4}-\d{2})\s*[–\-]\s*(?P<end>\d{4}-\d{2}|present)",
    re.I,
)


def _split_sections(text: str) -> dict[str, str]:
    headers = list(_HEADER_RE.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(headers):
        name = m.group("name").strip().lower()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        sections[name] = text[start:end]
    return sections


def _parse_sub_blocks(section_text: str) -> list[tuple[str, str]]:
    subs = list(_SUB_RE.finditer(section_text))
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(subs):
        header = m.group("name").strip()
        start = m.end()
        end = subs[i + 1].start() if i + 1 < len(subs) else len(section_text)
        blocks.append((header, section_text[start:end].strip()))
    return blocks


def _parse_bullets(body: str) -> list[str]:
    return [
        line.lstrip()[2:].strip()
        for line in body.splitlines()
        if line.lstrip().startswith("- ")
    ]


def parse_master_resume(
    text: str, source_id: str,
) -> list[Job | Project | Skill | Achievement]:
    sections = _split_sections(text)
    out: list[Job | Project | Skill | Achievement] = []

    for header, body in _parse_sub_blocks(sections.get("experience", "")):
        parts = [p.strip() for p in header.split("·")]
        role, company = parts[0], parts[1] if len(parts) > 1 else ""
        date_match = _DATE_RANGE_RE.search(parts[-1] if len(parts) > 2 else "")
        start_date = date_match.group("start") if date_match else "0000-00"
        end_raw = date_match.group("end") if date_match else None
        end_date = None if end_raw and end_raw.lower() == "present" else end_raw
        out.append(Job(
            id=f"job-{uuid.uuid4().hex[:8]}", source_id=source_id,
            company=company, role=role,
            start_date=start_date, end_date=end_date,
            bullets=_parse_bullets(body), evidence_span_ids=[],
        ))

    for header, body in _parse_sub_blocks(sections.get("projects", "")):
        name = header.split("—")[0].strip() if "—" in header else header
        out.append(Project(
            id=f"proj-{uuid.uuid4().hex[:8]}", source_id=source_id,
            name=name, role=None, technologies=[],
            bullets=_parse_bullets(body), evidence_span_ids=[],
        ))

    skills_text = sections.get("skills", "")
    for raw in re.split(r"[,\n]", skills_text):
        name = raw.strip().lstrip("- ").strip()
        if not name:
            continue
        out.append(Skill(
            id=f"sk-{uuid.uuid4().hex[:8]}", source_id=source_id,
            name=name, evidence_span_ids=[],
        ))

    return out

"""JobPostingParser: extracts structured requirements from raw posting text."""

from __future__ import annotations

import json
import uuid

from citevault.domain.models import JobPosting, Requirement, RequirementKind
from citevault.domain.ports import LLMPort

_SCHEMA = {
    "type": "object",
    "properties": {
        "role_title": {"type": ["string", "null"]},
        "company": {"type": ["string", "null"]},
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "kind": {"enum": ["must_have", "nice_to_have"]},
                    "priority": {"type": "integer"},
                },
                "required": ["text", "kind", "priority"],
            },
        },
    },
    "required": ["role_title", "company", "requirements"],
}

_SYSTEM = (
    "You are a job posting analyst. Your only task is to extract structured requirements "
    "from job postings. Categorise each requirement as must_have or nice_to_have and assign "
    "a priority from 1 (most critical) to 10 (least). Respond only with the requested JSON."
)

_PROMPT_TMPL = """\
Extract the structured requirements from the following job posting.

Job posting:
{text}

Return a JSON object matching this schema:
- role_title: the job title (string or null)
- company: company name (string or null)
- requirements: list of objects with:
    - text: requirement description
    - kind: "must_have" or "nice_to_have"
    - priority: integer 1 (most critical) to 10 (least)
"""


class JobPostingParser:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def parse(self, posting_text: str) -> JobPosting:
        raw = self._llm.complete(
            _PROMPT_TMPL.format(text=posting_text),
            schema=_SCHEMA,
            temperature=0.0,
            system=_SYSTEM,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned malformed JSON for job posting: {exc}") from exc
        requirements = []
        for r in data.get("requirements", []):
            try:
                req = Requirement(
                    id=f"req-{uuid.uuid4().hex[:8]}",
                    text=r["text"],
                    kind=RequirementKind(r["kind"]),
                    priority=r["priority"],
                )
            except (KeyError, ValueError):
                continue
            requirements.append(req)
        return JobPosting(
            id=f"jp-{uuid.uuid4().hex[:8]}",
            raw_text=posting_text,
            role_title=data.get("role_title"),
            company=data.get("company"),
            requirements=requirements,
        )

"""Compose a cover letter grounded in already-verified claims."""

from __future__ import annotations

import json

from citevault.domain.models import Claim, JobPosting
from citevault.domain.ports import LLMPort

_SCHEMA = {
    "type": "object",
    "properties": {
        "paragraphs": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["paragraphs"],
}

_SYSTEM = (
    "You are a professional cover letter writer. Your only task is to compose a concise, "
    "honest cover letter using only the verified facts provided. Do not invent skills, "
    "achievements, or experiences not on the list. Respond only with the requested JSON."
)

_PROMPT = """\
Compose a cover letter (3-4 short paragraphs) for the job posting below.

You may only reference the *verified facts* listed. Do not invent additional skills,
quantities, or experiences. If a fact isn't on the list, do not state it.

Job posting:
---
{posting}
---

Verified facts (use a subset, in your words):
{facts}

Return JSON: {{ "paragraphs": [ "para1", "para2", ... ] }}.
"""


class CoverLetterComposer:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def compose(self, posting: JobPosting, claims: list[Claim]) -> str:
        facts_block = "\n".join(f"- {c.text}" for c in claims) or "(none)"
        raw = self._llm.complete(
            _PROMPT.format(posting=posting.raw_text, facts=facts_block),
            schema=_SCHEMA, temperature=0.3, system=_SYSTEM,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned malformed JSON for cover letter: {exc}") from exc
        paragraphs = data.get("paragraphs", [])
        return "\n\n".join(str(p) for p in paragraphs) + "\n"

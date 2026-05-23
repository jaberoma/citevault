"""Stage A: draft claims with required citations."""

from __future__ import annotations

import json
import uuid

from citevault.domain.models import (
    Citation, Claim, ClaimStatus, ClaimType, Requirement, RetrievalCandidate,
)
from citevault.domain.ports import LLMPort

_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "claim_type": {
                        "enum": ["achievement", "skill", "experience", "education"]
                    },
                    "citations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "claim_type", "citations"],
            },
        }
    },
    "required": ["claims"],
}

_SYSTEM = (
    "You are a résumé claim drafter. Your only task is to produce concise, factual résumé "
    "bullet points that are directly supported by the provided evidence spans. Every claim "
    "must cite at least one span. Never invent facts, skills, or experiences not present in "
    "the evidence. Respond only with the requested JSON."
)

_PROMPT = """\
Draft résumé claims for a single job requirement.

Requirement: {requirement}

You may only cite spans from this retrieved evidence set. Each claim MUST cite at
least one span_id from the list. Never invent facts beyond the evidence.

Evidence spans:
{spans}

Return JSON: {{ "claims": [ ... ] }}. Each claim has text, claim_type
(achievement | skill | experience | education), and citations (list of span_ids).
If no evidence supports the requirement, return {{ "claims": [] }}.
"""


def _format_spans(candidates: list[RetrievalCandidate]) -> str:
    return "\n".join(
        f"  [{c.span_id}] {c.text}" for c in candidates if c.span_id
    ) or "  (no evidence)"


class StageADrafter:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def draft(
        self, requirement: Requirement, candidates: list[RetrievalCandidate],
    ) -> list[Claim]:
        allowed_ids = {c.span_id for c in candidates if c.span_id}
        prompt = _PROMPT.format(
            requirement=requirement.text, spans=_format_spans(candidates),
        )
        raw = self._llm.complete(prompt, schema=_SCHEMA, temperature=0.2, system=_SYSTEM)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned malformed JSON for claim draft: {exc}") from exc
        result: list[Claim] = []
        for c in data.get("claims", []):
            cited = [cid for cid in c.get("citations", []) if cid in allowed_ids]
            if not cited:
                continue  # reject claims with hallucinated citations
            text = c.get("text", "").strip()
            if not text:
                continue
            try:
                claim_type = ClaimType(c.get("claim_type", ""))
            except ValueError:
                continue
            result.append(Claim(
                id=f"cl-{uuid.uuid4().hex[:8]}",
                text=text,
                claim_type=claim_type,
                citations=[Citation(span_id=cid) for cid in cited],
                status=ClaimStatus.DRAFT,
            ))
        return result

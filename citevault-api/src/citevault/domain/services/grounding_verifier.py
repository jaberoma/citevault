"""Stage B verifier — checks whether a claim is supported by its cited spans."""

from __future__ import annotations

import json

from citevault.domain.models import Claim, Span, VerdictKind, VerificationResult
from citevault.domain.ports import LLMPort

_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"enum": ["SUPPORTS", "PARTIAL", "UNCLEAR", "CONTRADICTS"]},
        "confidence": {"type": "number"},
        "explanation": {"type": "string"},
    },
    "required": ["verdict", "confidence", "explanation"],
}

_SYSTEM = (
    "You are an evidence verifier. Your only task is to judge whether a résumé claim is "
    "supported by the provided evidence. Be conservative — when in doubt, do not vote "
    "SUPPORTS. You have no knowledge of the candidate beyond what the evidence states. "
    "Respond only with the requested JSON."
)

_PROMPT = """\
Given ONLY the evidence below, does it support the claim?

Verdicts:
  SUPPORTS    — evidence directly and unambiguously supports the claim
  PARTIAL     — evidence supports part of the claim, but the claim overstates
                or includes unsupported elements
  UNCLEAR     — evidence is ambiguous or insufficient
  CONTRADICTS — evidence contradicts the claim

Be conservative. When in doubt, do not vote SUPPORTS.

Claim: {claim}

Evidence:
{evidence}

Return JSON with verdict, confidence (0.0-1.0), and a brief explanation.
"""


class GroundingVerifier:
    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def verify(self, claim: Claim, spans: list[Span]) -> VerificationResult:
        evidence_block = "\n".join(f"- {s.text}" for s in spans) or "(none)"
        prompt = _PROMPT.format(claim=claim.text, evidence=evidence_block)
        raw = self._llm.complete(prompt, schema=_SCHEMA, temperature=0.1, system=_SYSTEM)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned malformed JSON for verification: {exc}") from exc
        try:
            verdict = VerdictKind(data["verdict"])
            confidence = float(data["confidence"])
            explanation = str(data["explanation"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"LLM returned unexpected verification payload: {exc}") from exc
        confidence = max(0.0, min(1.0, confidence))
        return VerificationResult(
            claim_id=claim.id,
            verdict=verdict,
            confidence=confidence,
            explanation=explanation,
        )

"""ClaimRewriter: applies refuse-or-rewrite policy with up to 2 rewrite attempts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from citevault.domain.models import (
    Claim, ClaimStatus, Span, VerdictKind, VerificationResult,
)
from citevault.domain.ports import LLMPort

MAX_REWRITES = 2

_SYSTEM = (
    "You are a résumé claim editor. Your only task is to conservatively rewrite a résumé "
    "claim so it stays within the bounds of what the evidence actually supports. Remove any "
    "overstatements, invented quantities, or unsupported adjectives. Return only the "
    "rewritten claim text — no explanation, no JSON, no preamble."
)

_REWRITE_PROMPT = """\
A claim was generated but the evidence only partially supports it (or is unclear).

Rewrite the claim conservatively, keeping ONLY what the evidence supports. Drop any
adjectives, quantifiers, or scope words the evidence does not justify. Return ONLY
the rewritten claim text, no explanation.

Original claim: {claim}
Verifier explanation: {explanation}
Evidence:
{evidence}
"""


@dataclass
class ClaimOutcome:
    claim: Claim
    final_status: ClaimStatus
    rewrite_attempts: int
    last_verdict: VerdictKind
    last_explanation: str


VerifierFn = Callable[[Claim, list[Span]], VerificationResult]


class ClaimRewriter:
    def __init__(self, llm: LLMPort, verifier: VerifierFn) -> None:
        self._llm = llm
        self._verify = verifier

    def process(self, claim: Claim, spans: list[Span]) -> ClaimOutcome:
        current = claim
        attempts = 0
        last_vr = self._verify(current, spans)

        while True:
            if last_vr.verdict == VerdictKind.SUPPORTS:
                status = ClaimStatus.REWRITTEN if attempts > 0 else ClaimStatus.VERIFIED
                return ClaimOutcome(
                    claim=current.model_copy(update={"status": status}),
                    final_status=status,
                    rewrite_attempts=attempts,
                    last_verdict=last_vr.verdict,
                    last_explanation=last_vr.explanation,
                )

            if last_vr.verdict == VerdictKind.CONTRADICTS or attempts >= MAX_REWRITES:
                return ClaimOutcome(
                    claim=current.model_copy(update={"status": ClaimStatus.REJECTED}),
                    final_status=ClaimStatus.REJECTED,
                    rewrite_attempts=attempts,
                    last_verdict=last_vr.verdict,
                    last_explanation=last_vr.explanation,
                )

            # PARTIAL or UNCLEAR → rewrite
            new_text = self._llm.complete(
                _REWRITE_PROMPT.format(
                    claim=current.text,
                    explanation=last_vr.explanation,
                    evidence="\n".join(f"- {s.text}" for s in spans),
                ),
                temperature=0.2,
                system=_SYSTEM,
            ).strip()
            if not new_text:
                return ClaimOutcome(
                    claim=current.model_copy(update={"status": ClaimStatus.REJECTED}),
                    final_status=ClaimStatus.REJECTED,
                    rewrite_attempts=attempts,
                    last_verdict=last_vr.verdict,
                    last_explanation="Rewriter returned empty text.",
                )
            current = current.model_copy(update={"text": new_text})
            attempts += 1
            last_vr = self._verify(current, spans)

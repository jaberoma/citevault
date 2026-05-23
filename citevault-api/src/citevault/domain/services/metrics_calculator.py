"""Compute eval metrics from a CaseRunSummary."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaseRunSummary:
    drafts_total: int
    first_pass_verified: int
    rewritten_verified: int
    rejected: int
    requirements_total: int
    requirements_met: int


@dataclass(frozen=True)
class Metrics:
    first_pass_grounding_rate: float
    final_grounding_rate: float
    rewrite_rate: float
    rejection_rate: float
    coverage_rate: float


def _safe(num: int, den: int) -> float:
    return 0.0 if den == 0 else num / den


def calculate_metrics(s: CaseRunSummary) -> Metrics:
    verified_total = s.first_pass_verified + s.rewritten_verified
    return Metrics(
        first_pass_grounding_rate=_safe(s.first_pass_verified, s.drafts_total),
        final_grounding_rate=_safe(verified_total, verified_total + s.rejected),
        rewrite_rate=_safe(s.rewritten_verified, s.drafts_total),
        rejection_rate=_safe(s.rejected, s.drafts_total),
        coverage_rate=_safe(s.requirements_met, s.requirements_total),
    )

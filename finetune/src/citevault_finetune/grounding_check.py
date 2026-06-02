"""Compare First-Pass Grounding Rate before vs. after a fine-tune."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegressionResult:
    passed: bool
    before_rate: float
    after_rate: float
    delta_pct: float
    tolerance_pct: float
    message: str


def check_regression(
    before_rate: float,
    after_rate: float,
    tolerance_pct: float = 3.0,
) -> RegressionResult:
    delta_pct = round((after_rate - before_rate) * 100, 6)
    passed = delta_pct >= -tolerance_pct
    if passed:
        msg = (
            f"First-Pass Grounding {before_rate:.1%} → {after_rate:.1%} "
            f"({delta_pct:+.1f}pp). within tolerance ({tolerance_pct}pp)."
        )
    else:
        msg = (
            f"First-Pass Grounding regressed: {before_rate:.1%} → "
            f"{after_rate:.1%} ({delta_pct:+.1f}pp), exceeding tolerance "
            f"of {tolerance_pct}pp."
        )
    return RegressionResult(
        passed=passed,
        before_rate=before_rate,
        after_rate=after_rate,
        delta_pct=delta_pct,
        tolerance_pct=tolerance_pct,
        message=msg,
    )

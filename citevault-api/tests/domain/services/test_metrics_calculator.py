"""Metrics calculation tests."""

from citevault.domain.services.metrics_calculator import (
    CaseRunSummary, Metrics, calculate_metrics,
)


def test_metrics_with_perfect_first_pass() -> None:
    summary = CaseRunSummary(
        drafts_total=10, first_pass_verified=10, rewritten_verified=0,
        rejected=0, requirements_total=5, requirements_met=5,
    )
    m = calculate_metrics(summary)
    assert m.first_pass_grounding_rate == 1.0
    assert m.coverage_rate == 1.0
    assert m.rejection_rate == 0.0


def test_metrics_with_mixed_outcomes() -> None:
    summary = CaseRunSummary(
        drafts_total=20, first_pass_verified=14, rewritten_verified=4,
        rejected=2, requirements_total=10, requirements_met=8,
    )
    m = calculate_metrics(summary)
    assert m.first_pass_grounding_rate == 0.7
    assert m.rewrite_rate == 0.2
    assert m.rejection_rate == 0.1
    assert m.coverage_rate == 0.8


def test_metrics_with_zero_drafts_returns_zero() -> None:
    summary = CaseRunSummary(
        drafts_total=0, first_pass_verified=0, rewritten_verified=0,
        rejected=0, requirements_total=5, requirements_met=0,
    )
    m = calculate_metrics(summary)
    assert m.first_pass_grounding_rate == 0.0
    assert m.coverage_rate == 0.0

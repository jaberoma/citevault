"""Grounding regression check: comparing First-Pass Grounding before/after fine-tune."""

from citevault_finetune.grounding_check import RegressionResult, check_regression


def test_regression_within_tolerance_passes() -> None:
    result = check_regression(before_rate=0.81, after_rate=0.79, tolerance_pct=3.0)
    assert result.passed is True
    assert "within tolerance" in result.message


def test_regression_outside_tolerance_fails() -> None:
    result = check_regression(before_rate=0.81, after_rate=0.72, tolerance_pct=3.0)
    assert result.passed is False
    assert "regressed" in result.message


def test_regression_exact_boundary_passes() -> None:
    result = check_regression(before_rate=0.80, after_rate=0.77, tolerance_pct=3.0)
    assert result.passed is True


def test_regression_improvement_passes() -> None:
    result = check_regression(before_rate=0.75, after_rate=0.80, tolerance_pct=3.0)
    assert result.passed is True
    assert result.delta_pct > 0

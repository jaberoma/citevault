"""Verifier faithfulness study: Cohen's kappa vs. human labels."""

import os
from pathlib import Path

import pytest

from citevault.eval.faithfulness import compute_kappa, load_labels


@pytest.mark.skipif(
    os.environ.get("CITEVAULT_SMOKE") != "1",
    reason="Real-LLM study; set CITEVAULT_SMOKE=1 to run.",
)
def test_verifier_kappa_above_threshold() -> None:
    csv = Path(__file__).parent / "faithfulness" / "labels.csv"
    labels = load_labels(str(csv))
    kappa = compute_kappa(labels)
    print(f"\nCohen's kappa: {kappa:.3f}")
    assert kappa >= 0.7, f"Verifier kappa {kappa:.3f} below 0.7 threshold"

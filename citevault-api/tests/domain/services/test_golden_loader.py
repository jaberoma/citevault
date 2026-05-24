"""Golden case loader tests."""

from pathlib import Path

import pytest

from citevault.domain.services.golden_loader import (
    ExpectedOutcome, GoldenCase, load_golden_case,
)


def test_load_case_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    case_dir = repo_root / "golden" / "case_01_backend_eng_kubernetes"
    case = load_golden_case(str(case_dir))
    assert case.case_id == "case_01_backend_eng_kubernetes"
    assert len(case.evidence_files) >= 1
    assert case.job_posting.strip().startswith("Senior Backend Engineer")
    assert case.minimum_first_pass_grounding_rate == 0.6
    rust_req = next(r for r in case.requirements if "Rust" in r.text)
    assert rust_req.expected == ExpectedOutcome.GAP_REPORTED
    assert "rust" in [s.lower() for s in (rust_req.gap_reason_must_mention or [])]


def test_load_case_with_missing_files_raises(tmp_path: Path) -> None:
    empty = tmp_path / "case_bad"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        load_golden_case(str(empty))

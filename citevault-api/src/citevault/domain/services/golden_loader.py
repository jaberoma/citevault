"""Load golden test cases (evidence + posting + expectations.yaml)."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ExpectedOutcome(str, Enum):
    SUPPORTED = "SUPPORTED"
    SUPPORTED_AFTER_REWRITE = "SUPPORTED_AFTER_REWRITE"
    GAP_REPORTED = "GAP_REPORTED"


class RequirementExpectation(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    expected: ExpectedOutcome
    must_cite_at_least_one_of: list[str] | None = None
    gap_reason_must_mention: list[str] | None = None


class GoldenCase(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    description: str = ""
    case_dir: str
    evidence_files: list[str] = Field(default_factory=list)
    job_posting: str
    requirements: list[RequirementExpectation]
    minimum_first_pass_grounding_rate: float = 0.0


def load_golden_case(case_dir: str) -> GoldenCase:
    base = Path(case_dir)
    exp_file = base / "expectations.yaml"
    job_file = base / "job_posting.txt"
    evidence_dir = base / "evidence"
    if not exp_file.is_file() or not job_file.is_file() or not evidence_dir.is_dir():
        raise FileNotFoundError(
            f"Case directory {case_dir} is missing expectations.yaml, "
            "job_posting.txt, or evidence/ subdirectory."
        )
    data = yaml.safe_load(exp_file.read_text())
    return GoldenCase(
        case_id=data["case_id"],
        description=data.get("description", ""),
        case_dir=str(base),
        evidence_files=[str(p) for p in sorted(evidence_dir.iterdir())
                        if p.is_file()],
        job_posting=job_file.read_text(),
        requirements=[
            RequirementExpectation.model_validate(r)
            for r in data["requirements"]
        ],
        minimum_first_pass_grounding_rate=float(
            data.get("minimum_first_pass_grounding_rate", 0.0)
        ),
    )

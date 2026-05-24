"""GapReporter compiles rejected claims + unmet requirements into a report."""

from citevault.domain.models import (
    Requirement, RequirementKind,
)
from citevault.domain.services.gap_reporter import GapReporter


def test_report_includes_unmet_requirements() -> None:
    reqs = [
        Requirement(id="r1", text="Rust", kind=RequirementKind.NICE_TO_HAVE, priority=5),
        Requirement(id="r2", text="K8s", kind=RequirementKind.MUST_HAVE, priority=1),
    ]
    met_req_ids = {"r2"}
    report = GapReporter().report(
        tailoring_id="t1", requirements=reqs, met_requirement_ids=met_req_ids,
        rejected_with_closest_evidence={},
    )
    assert len(report.entries) == 1
    assert "Rust" in report.entries[0].requirement_text


def test_report_includes_closest_evidence_when_available() -> None:
    reqs = [Requirement(id="r1", text="Rust experience",
                        kind=RequirementKind.NICE_TO_HAVE, priority=5)]
    rejected = {"r1": "I wrote some Rust in a tutorial."}
    report = GapReporter().report(
        tailoring_id="t1", requirements=reqs, met_requirement_ids=set(),
        rejected_with_closest_evidence=rejected,
    )
    assert report.entries[0].closest_evidence == "I wrote some Rust in a tutorial."

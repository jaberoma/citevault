"""GoldenCaseRunner single-case test with fakes."""

import json
from pathlib import Path

from citevault.application.run_evals import CaseEvaluation, GoldenCaseRunner
from citevault.domain.services.golden_loader import load_golden_case
from tests.fakes import FakeEmbedding, FakeReranker


class _SequencedLLM:
    """Returns responses in order; used to script drafter + verifier calls."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)

    def complete(self, prompt, schema=None, temperature=0.2, system=None):
        return self.responses.pop(0) if self.responses else "{}"


def test_runner_evaluates_case_against_expectations(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    case = load_golden_case(str(repo_root / "golden" / "case_01_backend_eng_kubernetes"))

    # Script posting parser, then all drafter calls return empty — testing runner glue.
    scripted = [
        json.dumps({
            "role_title": "Senior Backend Engineer", "company": None,
            "requirements": [
                {"text": r.text,
                 "kind": "must_have" if "Rust" not in r.text else "nice_to_have",
                 "priority": 1}
                for r in case.requirements
            ],
        }),
    ]
    scripted.extend([json.dumps({"claims": []})] * 30)

    runner = GoldenCaseRunner(
        embedder=FakeEmbedding(), reranker=FakeReranker(),
        llm=_SequencedLLM(scripted), db_path=str(tmp_path / "t.db"),
    )
    eval_: CaseEvaluation = runner.run_case(case)
    assert eval_.case_id == case.case_id
    # With no drafts produced, every requirement should appear in gaps.
    assert len(eval_.tailoring.gap_report.entries) == len(case.requirements)

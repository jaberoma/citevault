"""Run golden test cases through the tailoring pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from citevault.adapters.outbound.sqlite_repo import SqliteEvidenceRepository
from citevault.adapters.outbound.sqlite_retrieval import SqliteRetrieval
from citevault.application.index_evidence import IndexEvidence
from citevault.application.tailor_resume import TailorResume, TailoringResult
from citevault.domain.ports import EmbeddingPort, LLMPort, RerankerPort
from citevault.domain.services.golden_loader import (
    ExpectedOutcome, GoldenCase, RequirementExpectation,
)
from citevault.domain.services.job_posting_parser import JobPostingParser
from citevault.domain.services.metrics_calculator import Metrics, calculate_metrics


@dataclass(frozen=True)
class RequirementVerdict:
    expectation: RequirementExpectation
    actual: ExpectedOutcome
    passed: bool
    detail: str


@dataclass
class CaseEvaluation:
    case_id: str
    tailoring: TailoringResult
    metrics: Metrics
    requirement_verdicts: list[RequirementVerdict] = field(default_factory=list)
    case_passed: bool = False


@dataclass
class EvaluationResult:
    started_at: str
    case_evaluations: list[CaseEvaluation] = field(default_factory=list)
    aggregate_first_pass: float = 0.0
    overall_passed: bool = False


class GoldenCaseRunner:
    def __init__(
        self, embedder: EmbeddingPort, reranker: RerankerPort, llm: LLMPort,
        db_path: str,
    ) -> None:
        self._embedder = embedder
        self._reranker = reranker
        self._llm = llm
        self._db_path = db_path

    def run_case(self, case: GoldenCase) -> CaseEvaluation:
        case_db = str(Path(self._db_path).with_name(f"{case.case_id}.db"))
        repo = SqliteEvidenceRepository(case_db)
        IndexEvidence(repo=repo, embedder=self._embedder).run(
            str(Path(case.case_dir) / "evidence")
        )
        retrieval = SqliteRetrieval(db_path=case_db, embedder=self._embedder)

        posting = JobPostingParser(llm=self._llm).parse(case.job_posting)
        tailor = TailorResume(
            retrieval=retrieval, reranker=self._reranker, llm=self._llm,
            span_lookup=repo,
        )
        tailoring = tailor.run(posting, tailoring_id=f"eval-{uuid.uuid4().hex[:8]}")
        metrics = calculate_metrics(tailoring.summary)

        gap_texts = [e.requirement_text.lower() for e in tailoring.gap_report.entries]

        verdicts: list[RequirementVerdict] = []
        for exp in case.requirements:
            req_lc = exp.text.lower()
            in_gaps = any(req_lc in g for g in gap_texts)
            actual = (
                ExpectedOutcome.GAP_REPORTED if in_gaps
                else ExpectedOutcome.SUPPORTED
            )
            passed = (
                (exp.expected == ExpectedOutcome.GAP_REPORTED and in_gaps) or
                (exp.expected in (ExpectedOutcome.SUPPORTED,
                                  ExpectedOutcome.SUPPORTED_AFTER_REWRITE)
                 and not in_gaps)
            )
            detail = "in gap report" if in_gaps else "in verified claims"
            if exp.expected == ExpectedOutcome.GAP_REPORTED and exp.gap_reason_must_mention:
                match = next(
                    (e for e in tailoring.gap_report.entries
                     if req_lc in e.requirement_text.lower()), None,
                )
                if match:
                    combined = (
                        match.requirement_text + " " +
                        (match.closest_evidence or "") + " " +
                        match.neutral_suggestion
                    ).lower()
                    if not all(s.lower() in combined for s in exp.gap_reason_must_mention):
                        passed = False
                        detail = "gap reason missing required mentions"
            verdicts.append(RequirementVerdict(
                expectation=exp, actual=actual, passed=passed, detail=detail,
            ))

        case_passed = (
            all(v.passed for v in verdicts) and
            metrics.first_pass_grounding_rate >= case.minimum_first_pass_grounding_rate
        )
        return CaseEvaluation(
            case_id=case.case_id, tailoring=tailoring, metrics=metrics,
            requirement_verdicts=verdicts, case_passed=case_passed,
        )

    def run_all(self, cases: list[GoldenCase]) -> EvaluationResult:
        result = EvaluationResult(
            started_at=datetime.now(tz=timezone.utc).isoformat()
        )
        rates: list[float] = []
        for c in cases:
            ev = self.run_case(c)
            result.case_evaluations.append(ev)
            rates.append(ev.metrics.first_pass_grounding_rate)
        result.aggregate_first_pass = sum(rates) / len(rates) if rates else 0.0
        result.overall_passed = all(e.case_passed for e in result.case_evaluations)
        return result

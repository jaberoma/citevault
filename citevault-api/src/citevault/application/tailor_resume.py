"""TailorResume use case: orchestrates retrieval → draft → verify → rewrite → gaps."""

from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from citevault.domain.models import (
    Claim, ClaimStatus, GapReport, JobPosting, Requirement, RetrievalCandidate, Span,
)
from citevault.domain.ports import LLMPort, RerankerPort, RetrievalPort, TraceRepository
from citevault.domain.services.claim_rewriter import ClaimRewriter
from citevault.domain.services.drafter import StageADrafter
from citevault.domain.services.gap_reporter import GapReporter
from citevault.domain.services.grounding_verifier import GroundingVerifier
from citevault.domain.services.metrics_calculator import CaseRunSummary

logger = logging.getLogger(__name__)


class _SpanLookup(Protocol):
    def get_span(self, span_id: str) -> Span | None: ...


@dataclass
class TailoringResult:
    tailoring_id: str
    job_posting: JobPosting
    verified_claims: list[Claim] = field(default_factory=list)
    gap_report: GapReport = field(
        default_factory=lambda: GapReport(tailoring_id="", entries=[])
    )
    summary: CaseRunSummary = field(
        default_factory=lambda: CaseRunSummary(0, 0, 0, 0, 0, 0)
    )


class TailorResume:
    def __init__(
        self,
        retrieval: RetrievalPort,
        reranker: RerankerPort,
        llm: LLMPort,
        span_lookup: _SpanLookup,
        trace_repo: TraceRepository | None = None,
    ) -> None:
        self._retrieval = retrieval
        self._rerank = reranker
        self._llm = llm
        self._span_lookup = span_lookup
        self._trace_repo = trace_repo
        self._drafter = StageADrafter(llm)
        self._verifier = GroundingVerifier(llm)
        self._rewriter = ClaimRewriter(
            llm, verifier=lambda c, s: self._verifier.verify(c, s),
        )
        self._gaps = GapReporter()

    def _process_requirement(
        self, req: Requirement, i: int, total: int,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> tuple[list[Claim], str | None, dict[str, str], dict[str, int]]:
        verified: list[Claim] = []
        met_id: str | None = None
        rejected_info: dict[str, str] = {}
        counts = {"drafts": 0, "first_pass": 0, "rewritten": 0, "rejected": 0}

        req_start = time.time()
        logger.debug(f"[{i+1}/{total}] Processing requirement: {req.text[:50]}...")
        if on_event:
            on_event("requirement_started", {"req_id": req.id, "text": req.text})

        candidates = self._retrieval.hybrid_search(req.text, k=10)
        
        rerank_start = time.time()
        top: list[RetrievalCandidate] = self._rerank.rerank(
            req.text, candidates, top_n=5,
        )
        rerank_duration = time.time() - rerank_start
        logger.debug(f"Reranked {len(candidates)} candidates in {rerank_duration:.2f}s")
        if on_event:
            on_event("retrieval_done", {"req_id": req.id, "candidate_count": len(top)})

        if not top:
            logger.warning(f"No candidates found for requirement {req.id}")
            return verified, met_id, rejected_info, counts
        
        draft_start = time.time()
        drafts = self._drafter.draft(req, top)
        draft_duration = time.time() - draft_start
        logger.debug(f"Drafted {len(drafts)} claims in {draft_duration:.2f}s")
        
        if not drafts:
            logger.debug(f"No drafts generated for requirement {req.id}")
            rejected_info[req.id] = top[0].text
            return verified, met_id, rejected_info, counts
        
        req_verified = 0
        for claim in drafts:
            counts["drafts"] += 1
            maybe_spans = [
                self._span_lookup.get_span(c.span_id)
                for c in claim.citations if c.span_id
            ]
            spans = [s for s in maybe_spans if s is not None]
            
            verify_start = time.time()
            outcome = self._rewriter.process(claim, spans)
            verify_duration = time.time() - verify_start
            
            if outcome.final_status == ClaimStatus.VERIFIED:
                verified.append(outcome.claim)
                counts["first_pass"] += 1
                req_verified += 1
                logger.debug(f"Claim verified (first pass) in {verify_duration:.2f}s")
            elif outcome.final_status == ClaimStatus.REWRITTEN:
                verified.append(outcome.claim)
                counts["rewritten"] += 1
                req_verified += 1
                logger.debug(f"Claim rewritten and verified in {verify_duration:.2f}s")
            else:
                counts["rejected"] += 1
            if on_event:
                on_event("claim_finalized", {
                    "claim_id": outcome.claim.id,
                    "status": outcome.final_status.value,
                    "text": outcome.claim.text,
                    "verdict": outcome.last_verdict.value,
                })
        
        if req_verified > 0:
            met_id = req.id
            logger.info(f"Requirement met: {req.id} ({req_verified} claims) in {time.time() - req_start:.2f}s")
        else:
            rejected_info[req.id] = top[0].text
            logger.info(f"Requirement NOT met: {req.id} in {time.time() - req_start:.2f}s")

        return verified, met_id, rejected_info, counts

    def run(
        self, posting: JobPosting, tailoring_id: str,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> TailoringResult:
        logger.info(f"Starting tailoring {tailoring_id} for {len(posting.requirements)} requirements")
        start_time = time.time()
        if on_event:
            on_event("posting_parsed", {"requirements_count": len(posting.requirements)})

        total_reqs = len(posting.requirements)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self._process_requirement, req, i, total_reqs, on_event)
                for i, req in enumerate(posting.requirements)
            ]
            results = [f.result() for f in futures]

        verified: list[Claim] = []
        met: set[str] = set()
        rejected_closest: dict[str, str] = {}
        drafts_total = 0
        first_pass = 0
        rewritten = 0
        rejected = 0

        for req_claims, req_met_id, req_rejected, counts in results:
            verified.extend(req_claims)
            if req_met_id:
                met.add(req_met_id)
            rejected_closest.update(req_rejected)
            drafts_total += counts["drafts"]
            first_pass += counts["first_pass"]
            rewritten += counts["rewritten"]
            rejected += counts["rejected"]

        duration = time.time() - start_time
        logger.info(f"Tailoring {tailoring_id} finished in {duration:.2f}s. {len(met)}/{len(posting.requirements)} requirements met.")

        result = TailoringResult(
            tailoring_id=tailoring_id, job_posting=posting,
            verified_claims=verified,
            gap_report=self._gaps.report(
                tailoring_id=tailoring_id, requirements=posting.requirements,
                met_requirement_ids=met,
                rejected_with_closest_evidence=rejected_closest,
            ),
            summary=CaseRunSummary(
                drafts_total=drafts_total,
                first_pass_verified=first_pass,
                rewritten_verified=rewritten,
                rejected=rejected,
                requirements_total=len(posting.requirements),
                requirements_met=len(met),
            ),
        )

        # Save trace (optional — skipped if no trace_repo wired in)
        if self._trace_repo is None:
            return result
        trace_payload = {
            "tailoring_id": result.tailoring_id,
            "job_posting": json.loads(result.job_posting.model_dump_json()),
            "verified_claims": [json.loads(c.model_dump_json()) for c in result.verified_claims],
            "gap_report": json.loads(result.gap_report.model_dump_json()),
        }
        self._trace_repo.save_trace(json.dumps(trace_payload), tailoring_id)

        return result

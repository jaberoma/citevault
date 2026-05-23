"""Compute Cohen's kappa for the verifier against human labels."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from citevault.adapters.outbound.ollama_llm import OllamaLLM
from citevault.domain.models import (
    Citation, Claim, ClaimStatus, ClaimType, Span, VerdictKind,
)
from citevault.domain.services.grounding_verifier import GroundingVerifier


@dataclass(frozen=True)
class Label:
    id: int
    claim: str
    evidence: str
    true_verdict: VerdictKind


def load_labels(csv_path: str) -> list[Label]:
    out: list[Label] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(Label(
                id=int(row["id"]),
                claim=row["claim"],
                evidence=row["evidence"],
                true_verdict=VerdictKind(row["true_verdict"]),
            ))
    return out


def _cohens_kappa(labels: list[VerdictKind], preds: list[VerdictKind]) -> float:
    n = len(labels)
    if n == 0:
        return 0.0
    cats = list({*labels, *preds})
    agree = sum(1 for a, b in zip(labels, preds) if a == b) / n
    p_chance = sum(
        (labels.count(c) / n) * (preds.count(c) / n)
        for c in cats
    )
    if p_chance >= 1:
        return 1.0
    return (agree - p_chance) / (1 - p_chance)


def compute_kappa(labels: list[Label]) -> float:
    llm = OllamaLLM(
        base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
        model=os.environ.get("CITEVAULT_MODEL", "gemma4:e4b"),
    )
    verifier = GroundingVerifier(llm=llm)
    truths: list[VerdictKind] = []
    preds: list[VerdictKind] = []
    for lab in labels:
        claim = Claim(
            id=f"c{lab.id}", text=lab.claim,
            claim_type=ClaimType.ACHIEVEMENT,
            citations=[Citation(span_id=f"sp{lab.id}")],
            status=ClaimStatus.DRAFT,
        )
        span = Span(
            id=f"sp{lab.id}", source_id="s",
            start_offset=0, end_offset=len(lab.evidence),
            text=lab.evidence,
        )
        vr = verifier.verify(claim, [span])
        truths.append(lab.true_verdict)
        preds.append(vr.verdict)
    return _cohens_kappa(truths, preds)

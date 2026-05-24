"""Tailor HTTP routes — POST to start, GET to retrieve, SSE for progress."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from citevault.adapters.inbound.http.settings_routes import load_settings
from citevault.adapters.outbound.markdown_renderer import (
    render_gaps_markdown, render_resume_markdown, render_resume_pdf_html,
)
from citevault.adapters.outbound.pdf_renderer import html_to_pdf
from citevault.composition.container import Container
from citevault.domain.models import Job
from citevault.domain.services.cover_letter import CoverLetterComposer
from citevault.domain.services.job_posting_parser import JobPostingParser

router = APIRouter(prefix="/api/tailor", tags=["tailor"])


class TailorRequest(BaseModel):
    job_posting: str
    naive_compare: bool = False


# Simple in-memory tailoring store (single-user local app — fine for v1).
_STORE: dict[str, dict[str, Any]] = {}
_QUEUES: dict[str, asyncio.Queue] = {}
_STORE_MAX = 100


def _evict_store() -> None:
    while len(_STORE) > _STORE_MAX:
        _STORE.pop(next(iter(_STORE)))


@router.post("", status_code=202)
async def start_tailoring(req: TailorRequest, request: Request) -> dict:
    container: Container = request.app.state.container
    if not container.is_ready:
        raise HTTPException(503, detail="Models are loading, please try again in a moment")
    tailoring_id = f"t-{uuid.uuid4().hex[:8]}"
    queue: asyncio.Queue = asyncio.Queue()
    _QUEUES[tailoring_id] = queue
    _STORE[tailoring_id] = {"status": "running"}
    _evict_store()
    loop = asyncio.get_event_loop()
    current_model = load_settings().model
    container.llm._model = current_model

    def emit(event: str, data: dict[str, Any]) -> None:
        msg = json.dumps({"event": event, "data": data})
        loop.call_soon_threadsafe(queue.put_nowait, msg)

    def background() -> None:
        try:
            logger.info("Tailoring %s started (naive_compare=%s, model=%s)", tailoring_id, req.naive_compare, current_model)
            posting = JobPostingParser(llm=container.llm).parse(req.job_posting)
            _STORE[tailoring_id]["job_role"] = posting.role_title
            logger.info("Tailoring %s — role: %s, %d requirements", tailoring_id, posting.role_title, len(posting.requirements))
            emit("started", {"tailoring_id": tailoring_id})

            result = container.tailor_resume.run(posting, tailoring_id, on_event=emit)

            naive_md: str | None = None
            if req.naive_compare:
                sources = container.evidence_repo.list_sources()
                evidence_parts = []
                for src in sources:
                    spans = container.evidence_repo.list_spans_for_source(src.id)
                    if spans:
                        evidence_parts.append(
                            f"### {src.path}\n" + "\n".join(s.text for s in spans)
                        )
                evidence_text = "\n\n".join(evidence_parts)
                naive_prompt = (
                    "You are a professional résumé writer. Using the candidate's background "
                    "below, tailor a résumé for the job posting.\n\n"
                    f"Candidate background:\n{evidence_text}\n\n"
                    f"Job posting:\n{req.job_posting}\n"
                )
                try:
                    naive_md = container.llm.complete(naive_prompt, temperature=0.4)
                except Exception as naive_exc:
                    logger.warning("Naive comparison failed for %s: %s", tailoring_id, naive_exc)
                    naive_md = None

            span_texts = {
                ci.span_id: container.evidence_repo.get_span(ci.span_id).text  # type: ignore[union-attr]
                for cl in result.verified_claims
                for ci in cl.citations
                if ci.span_id and container.evidence_repo.get_span(ci.span_id)
            }
            cited_source_ids = {
                container.evidence_repo.get_span(ci.span_id).source_id  # type: ignore[union-attr]
                for cl in result.verified_claims
                for ci in cl.citations
                if ci.span_id and container.evidence_repo.get_span(ci.span_id)
            }
            cited_jobs: list[Job] = [
                entry
                for source_id in cited_source_ids
                for entry in container.evidence_repo.list_structured_entries(source_id)
                if isinstance(entry, Job)
            ]
            cover = CoverLetterComposer(container.llm).compose(posting, result.verified_claims)
            resume_md = render_resume_markdown(result, span_texts, cited_jobs=cited_jobs)
            gaps_md = render_gaps_markdown(result)
            summary = result.summary

            _STORE[tailoring_id] = {
                "tailoring_id": tailoring_id,
                "status": "complete",
                "job_role": posting.role_title,
                "resume_md": resume_md,
                "cover_letter_md": cover,
                "gaps_md": gaps_md,
                "verified_claims": [
                    {"id": cl.id, "text": cl.text,
                     "citations": [ci.span_id for ci in cl.citations if ci.span_id]}
                    for cl in result.verified_claims
                ],
                "gap_report": [e.model_dump() for e in result.gap_report.entries],
                "span_texts": span_texts,
                "summary": {
                    "drafts_total": summary.drafts_total,
                    "first_pass_verified": summary.first_pass_verified,
                    "rewritten_verified": summary.rewritten_verified,
                    "rejected": summary.rejected,
                    "requirements_total": summary.requirements_total,
                    "requirements_met": summary.requirements_met,
                },
                "naive_md": naive_md,
                "pdf_ready": False,
            }
            s = _STORE[tailoring_id]["summary"]
            logger.info(
                "Tailoring %s complete — %d/%d requirements met, %d verified claims",
                tailoring_id, s["requirements_met"], s["requirements_total"],
                len(_STORE[tailoring_id]["verified_claims"]),
            )
            emit("complete", {"tailoring_id": tailoring_id})

            def _generate_pdf() -> None:
                db_path = os.environ.get("CITEVAULT_DB", "./citevault.db")
                pdf_path = os.path.join(str(Path(db_path).parent), f"{tailoring_id}.pdf")
                try:
                    html_to_pdf(render_resume_pdf_html(result, span_texts, cited_jobs=cited_jobs), pdf_path)
                    _STORE[tailoring_id]["pdf_path"] = pdf_path
                    _STORE[tailoring_id]["pdf_ready"] = True
                    logger.info("PDF ready for tailoring %s: %s", tailoring_id, pdf_path)
                except Exception as exc:
                    logger.warning("PDF generation failed for %s: %s", tailoring_id, exc)

            threading.Thread(target=_generate_pdf, daemon=True).start()
        except Exception as e:
            logger.error("Tailoring %s failed: %s", tailoring_id, e, exc_info=True)
            _STORE[tailoring_id] = {"status": "error", "error": str(e),
                                     "tailoring_id": tailoring_id}
            emit("error", {"message": str(e)})
        finally:
            _QUEUES.pop(tailoring_id, None)

    threading.Thread(target=background, daemon=True).start()
    return {"tailoring_id": tailoring_id}


@router.get("/{tailoring_id}")
def get_tailoring(tailoring_id: str) -> dict:
    if tailoring_id not in _STORE:
        raise HTTPException(404, detail="tailoring not found")
    return _STORE[tailoring_id]


@router.get("/{tailoring_id}/pdf")
def download_pdf(tailoring_id: str) -> FileResponse:
    entry = _STORE.get(tailoring_id)
    if not entry or not entry.get("pdf_ready"):
        raise HTTPException(404, detail="PDF not available")
    return FileResponse(
        entry["pdf_path"],
        media_type="application/pdf",
        filename="citevault-resume.pdf",
    )


@router.get("/{tailoring_id}/stream")
async def stream(tailoring_id: str) -> EventSourceResponse:
    if tailoring_id not in _QUEUES:
        raise HTTPException(404, detail="tailoring not found")
    queue = _QUEUES[tailoring_id]

    async def events():
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                continue
            yield {"data": msg}
            parsed = json.loads(msg)
            if parsed["event"] in ("complete", "error"):
                break

    return EventSourceResponse(events())


@router.get("")
def list_tailorings() -> dict:
    return {
        "tailorings": [
            {"tailoring_id": tid, "status": v.get("status"),
             "summary": v.get("summary"),
             "job_role": v.get("job_role")}
            for tid, v in _STORE.items()
        ]
    }

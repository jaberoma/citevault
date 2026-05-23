"""Evidence-management HTTP routes."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile

from citevault.adapters.outbound.sqlite_repo import SqliteEvidenceRepository

from citevault.application.index_evidence import IndexEvidence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evidence", tags=["evidence"])


def _repo() -> SqliteEvidenceRepository:
    return SqliteEvidenceRepository(os.environ.get("CITEVAULT_DB", "./citevault.db"))


@router.get("")
def list_evidence() -> dict:
    repo = _repo()
    return {
        "sources": [
            {
                "id": s.id, "kind": s.kind.value, "path": s.path,
                "created_at": s.created_at.isoformat(),
            }
            for s in repo.list_sources()
        ]
    }


@router.post("/source", status_code=201)
async def upload_source(request: Request, file: UploadFile = File(...)) -> dict:
    if not request.app.state.container.is_ready:
        raise HTTPException(503, detail="Models are loading, please try again in a moment")
    if not file.filename:
        raise HTTPException(400, detail="filename required")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".md", ".txt", ".pdf"}:
        raise HTTPException(415, detail=f"unsupported file type: {suffix}")

    logger.info("Upload requested: %s", file.filename)
    with tempfile.TemporaryDirectory() as tdir:
        dst = Path(tdir) / file.filename
        dst.write_bytes(await file.read())
        repo = _repo()
        use_case = IndexEvidence(repo=repo, embedder=request.app.state.container.embedder)
        use_case.run(tdir)

    sources = _repo().list_sources()
    new_source = max(sources, key=lambda s: s.created_at)
    logger.info("Upload complete: %s → %s (%s)", file.filename, new_source.id, new_source.kind.value)
    return {"id": new_source.id, "kind": new_source.kind.value,
            "path": new_source.path}


@router.delete("/source/{source_id}", status_code=204)
def delete_source(source_id: str) -> Response:
    logger.info("Deleting source: %s", source_id)
    _repo().delete_source(source_id)
    return Response(status_code=204)


@router.get("/source/{source_id}")
def get_source_detail(source_id: str) -> dict:
    repo = _repo()
    src = next((s for s in repo.list_sources() if s.id == source_id), None)
    if src is None:
        raise HTTPException(404, detail="source not found")
    spans = [
        {"id": sp.id, "start_offset": sp.start_offset, "end_offset": sp.end_offset, "text": sp.text}
        for sp in repo.list_spans_for_source(source_id)
    ]
    return {
        "id": src.id, "kind": src.kind.value, "path": src.path,
        "text": src.text, "spans": spans,
    }

"""Ollama proxy routes — exposes available models to the UI."""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/ollama", tags=["ollama"])


@router.get("/models")
def list_models() -> dict:
    ollama = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    try:
        r = httpx.get(f"{ollama}/api/tags", timeout=5.0)
        r.raise_for_status()
        models = [
            {
                "name": m["name"],
                "size": m["size"],
                "family": m["details"]["family"],
            }
            for m in r.json().get("models", [])
        ]
    except Exception:
        models = []
    return {"models": models}

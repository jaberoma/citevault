"""Settings HTTP routes — persisted in the SQLite settings table."""

from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from citevault.adapters.outbound.sqlite.connection import open_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])


class Settings(BaseModel):
    model: str = "gemma4:e4b"


_KEY = "user_settings"


def _conn():
    return open_db(os.environ.get("CITEVAULT_DB", "./citevault.db"))


def load_settings() -> Settings:
    cur = _conn().execute("SELECT value FROM settings WHERE key = ?", (_KEY,))
    row = cur.fetchone()
    if row is None:
        return Settings()
    return Settings.model_validate_json(row[0])


def _save(s: Settings) -> None:
    c = _conn()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (_KEY, s.model_dump_json()),
    )
    c.commit()


def _ollama_host() -> str:
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _check_model_available(model: str) -> bool:
    try:
        r = httpx.post(f"{_ollama_host()}/api/show", json={"model": model}, timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


@router.get("")
def get_settings() -> dict:
    s = load_settings()
    return {**s.model_dump(), "available": _check_model_available(s.model)}


@router.put("")
def put_settings(payload: Settings) -> dict:
    try:
        r = httpx.post(f"{_ollama_host()}/api/show", json={"model": payload.model}, timeout=5.0)
        if r.status_code == 404:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Model '{payload.model}' is not downloaded in Ollama. "
                    f"Run: docker compose exec ollama ollama pull {payload.model}"
                ),
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Ollama unreachable — allow save; tailoring will fail at inference time
    logger.info("Settings updated: model=%s", payload.model)
    _save(payload)
    return {**payload.model_dump(), "available": True}

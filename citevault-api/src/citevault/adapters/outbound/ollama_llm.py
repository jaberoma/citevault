"""Ollama HTTP client adapter implementing LLMPort."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _strip_fences(text: str) -> str:
    """Remove optional markdown code fences around JSON responses."""
    stripped = text.strip()
    for fence in ("```json\n", "```\n", "```json", "```"):
        if stripped.startswith(fence):
            stripped = stripped[len(fence):]
            break
    if stripped.endswith("```"):
        stripped = stripped[:-3]
    return stripped.strip()


def _repair_json_escapes(text: str) -> str:
    """Escape lone backslashes that are not valid JSON escape sequences."""
    return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)


class OllamaLLM:
    def __init__(
        self,
        base_url: str | None = None,
        model: str = "gemma4:e4b",
        timeout_s: float = 3600.0,
        num_ctx: int = 8192,
    ) -> None:
        self._base_url = (
            base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")
        self._model = model
        self._num_ctx = num_ctx
        self._client = httpx.Client(timeout=timeout_s)

    def complete(
        self, prompt: str, schema: dict[str, Any] | None = None,
        temperature: float = 0.2, system: str | None = None,
        num_ctx: int | None = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        options: dict[str, Any] = {"temperature": temperature, "num_ctx": num_ctx if num_ctx is not None else self._num_ctx}
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        t0 = time.monotonic()
        resp = self._client.post(f"{self._base_url}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        content = str(resp.json()["choices"][0]["message"]["content"])
        if schema is not None:
            content = _repair_json_escapes(_strip_fences(content))
        logger.info(
            "LLM %s | sys=%s prompt=%d chars → %d chars in %.1fs",
            self._model, system is not None, len(prompt), len(content),
            time.monotonic() - t0,
        )
        return content

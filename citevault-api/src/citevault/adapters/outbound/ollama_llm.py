"""Ollama HTTP client adapter implementing LLMPort."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OllamaLLM:
    def __init__(
        self,
        base_url: str | None = None,
        model: str = "gemma4:e4b",
        timeout_s: float = 3600.0,
    ) -> None:
        self._base_url = (
            base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")
        self._model = model
        self._client = httpx.Client(timeout=timeout_s)

    def complete(
        self, prompt: str, schema: dict[str, Any] | None = None,
        temperature: float = 0.2, system: str | None = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if schema is not None:
            payload["response_format"] = {"type": "json_object"}
        t0 = time.monotonic()
        resp = self._client.post(f"{self._base_url}/v1/chat/completions", json=payload)
        resp.raise_for_status()
        content = str(resp.json()["choices"][0]["message"]["content"])
        logger.info(
            "LLM %s | sys=%s prompt=%d chars → %d chars in %.1fs",
            self._model, system is not None, len(prompt), len(content),
            time.monotonic() - t0,
        )
        return content

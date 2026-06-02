"""Build (synthetic_prompt, real_user_writing) pairs from a folder of samples."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import httpx

MIN_WORDS = 100


@dataclass(frozen=True)
class WritingSample:
    path: str
    text: str


@dataclass(frozen=True)
class TrainingPair:
    prompt: str
    response: str


class SyntheticPromptLLM(Protocol):
    def synthesize_prompt(self, text: str) -> str: ...


def _passes_filter(text: str) -> bool:
    return len(text.split()) >= MIN_WORDS


def _load_samples(folder: str) -> list[WritingSample]:
    out: list[WritingSample] = []
    for p in sorted(Path(folder).iterdir()):
        if p.suffix.lower() in {".md", ".txt"} and p.is_file():
            text = p.read_text(encoding="utf-8")
            out.append(WritingSample(path=str(p), text=text))
    return out


class OllamaSyntheticPromptLLM:
    """Generates the prompt that 'would have produced' a given writing sample."""

    _SYS_PROMPT = (
        "Given a piece of writing by a specific author, write the prompt or "
        "instruction that would have naturally produced it. Return ONLY the prompt, "
        "one to three sentences, no quotes, no preamble."
    )

    def __init__(
        self,
        base_url: str | None = None,
        model: str = "gemma4:e4b",
    ) -> None:
        self._url = (
            base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")
        self._model = model

    def synthesize_prompt(self, text: str) -> str:
        payload = {
            "model": self._model,
            "prompt": f"{self._SYS_PROMPT}\n\nWriting:\n---\n{text[:2000]}\n---",
            "stream": False,
            "options": {"temperature": 0.3},
        }
        r = httpx.post(f"{self._url}/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["response"].strip()


class DatasetBuilder:
    def __init__(self, llm: SyntheticPromptLLM) -> None:
        self._llm = llm

    def build(self, folder: str) -> list[TrainingPair]:
        samples = _load_samples(folder)
        kept = [s for s in samples if _passes_filter(s.text)]
        pairs: list[TrainingPair] = []
        for s in kept:
            prompt = self._llm.synthesize_prompt(s.text)
            pairs.append(TrainingPair(prompt=prompt, response=s.text))
        return pairs

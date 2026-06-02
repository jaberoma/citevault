"""Pairwise voice-fidelity judge: which of A or B sounds more like the reference?"""

from __future__ import annotations

import os
from typing import Protocol


class PairwiseJudge(Protocol):
    def judge(self, reference: str, a_text: str, b_text: str) -> str: ...


class OllamaJudge:
    _PROMPT = (
        "You are a writing-style judge. Reference passage by an author follows.\n\n"
        "Reference:\n---\n{ref}\n---\n\nTwo candidate passages:\n\n"
        "A:\n---\n{a}\n---\n\nB:\n---\n{b}\n---\n\n"
        "Which candidate (A or B) sounds more like the reference author's voice?\n"
        "Answer with ONE letter, A or B, nothing else."
    )

    def __init__(self, base_url: str | None = None, model: str = "gemma4:e4b") -> None:
        import httpx

        self._url = (
            base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")
        self._model = model
        self._httpx = httpx

    def judge(self, reference: str, a_text: str, b_text: str) -> str:
        prompt = self._PROMPT.format(ref=reference, a=a_text, b=b_text)
        r = self._httpx.post(
            f"{self._url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0},
            },
            timeout=120,
        )
        r.raise_for_status()
        out = r.json()["response"].strip().upper()
        return "A" if out.startswith("A") else "B"


class VoiceEvaluator:
    def __init__(self, judge: PairwiseJudge) -> None:
        self._judge = judge

    def win_rate(
        self,
        references: list[str],
        finetuned_outputs: list[str],
        base_outputs: list[str],
    ) -> float:
        if not references:
            return 0.0
        wins = sum(
            1
            for ref, ft, base in zip(references, finetuned_outputs, base_outputs)
            if self._judge.judge(ref, a_text=ft, b_text=base) == "A"
        )
        return wins / len(references)

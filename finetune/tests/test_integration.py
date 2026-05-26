"""Integration tests — require a running Ollama instance.

Opt-in: CITEVAULT_FINETUNE_INTEGRATION=1 pytest tests/test_integration.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_INTEGRATION = os.environ.get("CITEVAULT_FINETUNE_INTEGRATION") == "1"
_SKIP = pytest.mark.skipif(not _INTEGRATION, reason="Opt-in with CITEVAULT_FINETUNE_INTEGRATION=1.")

# Enough prose to clear the 100-word filter (MIN_WORDS = 100)
_SAMPLE_TEXT = (
    "Software engineer with over twenty years of experience in the design and development "
    "of complex, high-performance systems across diverse business domains. "
    "My expertise lies in domain-driven design, event-driven architectures, and microservices, "
    "which I leverage to build scalable, maintainable, and robust software systems. "
    "Particularly skilled in leading teams with an Agile mindset, guiding projects from concept "
    "through implementation, and ensuring high standards of quality and performance. "
    "My primary focus is on leveraging architectural best practices to design systems that are "
    "both flexible and future-proof, delivering innovative and resilient solutions that meet "
    "real business needs. "
    "I have significant experience with cloud infrastructure and distributed systems, "
    "and I care deeply about code quality, testability, and long-term maintainability."
)


@_SKIP
def test_dataset_builder_produces_pairs_with_real_ollama(tmp_path: Path) -> None:
    from citevault_finetune.dataset_builder import DatasetBuilder, OllamaSyntheticPromptLLM

    (tmp_path / "sample.txt").write_text(_SAMPLE_TEXT)
    pairs = DatasetBuilder(llm=OllamaSyntheticPromptLLM()).build(str(tmp_path))

    assert len(pairs) == 1
    assert len(pairs[0].prompt) > 0
    assert pairs[0].response == _SAMPLE_TEXT


@_SKIP
def test_dataset_builder_filters_short_samples(tmp_path: Path) -> None:
    from citevault_finetune.dataset_builder import DatasetBuilder, OllamaSyntheticPromptLLM

    (tmp_path / "short.txt").write_text("Too short.")
    (tmp_path / "long.txt").write_text(_SAMPLE_TEXT)
    pairs = DatasetBuilder(llm=OllamaSyntheticPromptLLM()).build(str(tmp_path))

    assert len(pairs) == 1


@_SKIP
def test_ollama_judge_returns_valid_verdict() -> None:
    from citevault_finetune.voice_evaluator import OllamaJudge

    judge = OllamaJudge()
    reference = "I build systems that are robust, scalable and maintainable."
    a_text = "I design robust and scalable systems with a focus on maintainability."
    b_text = "Systems are built using various modern technologies and frameworks."

    result = judge.judge(reference=reference, a_text=a_text, b_text=b_text)

    assert result in ("A", "B")


@_SKIP
def test_voice_evaluator_win_rate_is_in_range() -> None:
    from citevault_finetune.voice_evaluator import OllamaJudge, VoiceEvaluator

    evaluator = VoiceEvaluator(judge=OllamaJudge())
    references = [
        "I build systems that are robust, scalable and maintainable.",
        "My focus is on clean architecture and pragmatic design decisions.",
    ]
    finetuned = [
        "I design robust and scalable systems with a focus on maintainability.",
        "Clean architecture and pragmatic design are at the core of my approach.",
    ]
    base = [
        "Systems are built using various modern technologies and frameworks.",
        "Design patterns and software architecture are important considerations.",
    ]

    rate = evaluator.win_rate(references=references, finetuned_outputs=finetuned, base_outputs=base)

    assert 0.0 <= rate <= 1.0

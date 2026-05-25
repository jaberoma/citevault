"""Dataset builder tests using a stub Ollama client."""

from pathlib import Path

import pytest

from citevault_finetune.dataset_builder import (
    DatasetBuilder,
    WritingSample,
    _passes_filter,
)


def test_filter_rejects_short_samples() -> None:
    assert not _passes_filter("This is too short.")
    assert _passes_filter(" ".join(["word"] * 150))


def test_build_dataset_pairs_prompts_with_writing(tmp_path: Path) -> None:
    sample_dir = tmp_path / "voice"
    sample_dir.mkdir()
    (sample_dir / "post1.md").write_text(" ".join(["word"] * 200))
    (sample_dir / "post2.md").write_text("short — should be skipped")

    class StubLLM:
        def __init__(self) -> None:
            self.calls = 0

        def synthesize_prompt(self, text: str) -> str:
            self.calls += 1
            return f"Synthetic prompt for: {text[:30]}"

    builder = DatasetBuilder(llm=StubLLM())
    pairs = builder.build(str(sample_dir))
    assert len(pairs) == 1
    assert pairs[0].prompt.startswith("Synthetic prompt for:")
    assert "word" in pairs[0].response


def test_build_dataset_skips_non_text_files(tmp_path: Path) -> None:
    sample_dir = tmp_path / "voice"
    sample_dir.mkdir()
    (sample_dir / "valid.md").write_text(" ".join(["word"] * 200))
    (sample_dir / "image.png").write_bytes(b"\x89PNG\r\n")

    class StubLLM:
        def synthesize_prompt(self, text: str) -> str:
            return "prompt"

    builder = DatasetBuilder(llm=StubLLM())
    pairs = builder.build(str(sample_dir))
    assert len(pairs) == 1

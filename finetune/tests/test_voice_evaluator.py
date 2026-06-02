"""Pairwise voice-fidelity evaluation tests."""

from citevault_finetune.voice_evaluator import VoiceEvaluator


class StubJudge:
    """Returns A when the finetuned text contains a sentinel; B otherwise."""

    def judge(self, reference: str, a_text: str, b_text: str) -> str:
        return "A" if "[finetuned]" in a_text else "B"


def test_evaluator_returns_pairwise_win_rate() -> None:
    references = ["a sample of my real writing — informal, technical, terse"] * 3
    base = ["Generic AI-sounding paragraph."] * 3
    finetuned = ["[finetuned] My voice paragraph."] * 3
    ev = VoiceEvaluator(judge=StubJudge())
    rate = ev.win_rate(references, finetuned_outputs=finetuned, base_outputs=base)
    assert rate == 1.0


def test_evaluator_handles_mixed_results() -> None:
    references = ["ref"] * 4
    base = ["b"] * 4
    finetuned = ["[finetuned] x", "y", "[finetuned] x", "y"]
    ev = VoiceEvaluator(judge=StubJudge())
    rate = ev.win_rate(references, finetuned_outputs=finetuned, base_outputs=base)
    assert rate == 0.5


def test_evaluator_empty_input_returns_zero() -> None:
    ev = VoiceEvaluator(judge=StubJudge())
    assert ev.win_rate([], finetuned_outputs=[], base_outputs=[]) == 0.0

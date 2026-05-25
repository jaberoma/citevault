# Voice Fine-Tune — Quick Guide

Voice fine-tuning is an optional add-on. It produces a personalized Gemma
variant (`citevault-voice`) adapted to your writing style. Cover letters and
résumé summaries gain the most.

## When to use it

- You have at least 100 writing samples (cover letters, blog posts, etc.) totalling
  ≥ 50k tokens.
- Generic AI cover-letter language is the friction you most want to remove.

## When NOT to use it

- You only have a handful of samples — fine-tuning at low data overfits and may
  hurt grounding more than it helps voice.
- You're new to PyTorch and don't have the hardware budget right now — the base
  `gemma4:e4b` is already very capable and delivers the core Citevault value.

## Success gates

The pipeline is considered successful when both axes pass:

1. **Voice fidelity** — pairwise LLM-as-judge win rate ≥ 65% vs base model
2. **Grounding regression** — First-Pass Grounding Rate must not drop more than
   3 percentage points vs the baseline

See `finetune/README.md` for the operational steps.

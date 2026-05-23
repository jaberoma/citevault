# Citevault — Project Inception

**Date:** 2026-05-11
**Status:** Shaping complete. Design spec is the next artifact.
**Purpose of this document:** Hand off the *outcome and rationale* of the shaping phase so a fresh session — possibly on a different machine, possibly with new agents — can pick up without re-litigating the decision.

---

## What we're building

**Citevault** is a local-first AI tool that produces tailored résumés and cover letters where **every claim is provably grounded in evidence the user has provided** (master résumé, project READMEs, blog posts, writing samples, performance reviews). If the model cannot ground a claim in a source, it refuses to write it and flags the gap honestly.

*AI that won't lie about your experience.*

Built on Google's Gemma 4 (open-weight, local inference via Ollama). No API keys required. No data leaves the machine.

---

## Why

Most AI résumé tools tend to hallucinate. Ask one to tailor your résumé for a role requiring "Rust experience" and it will likely invent a Rust project you never worked on. Citevault is designed as the structural opposite — every bullet either cites a source or is refused.

The privacy angle follows naturally: career data is sensitive. Local-first inference means the project author is never a data controller.

---

## First version scope

- **Evidence library** — upload and index source material (master résumé, project READMEs, blog posts, performance reviews, anything text-based)
- **Tailoring engine** — paste a job posting; the engine retrieves relevant evidence, verifies each claim against it, and produces a grounded résumé and cover letter
- **Gap report** — claims the engine cannot ground are refused and listed, not fabricated
- **Naive comparison mode** — side-by-side view of the grounded output against an unconstrained AI run, making the grounding value immediately visible
- **React UI** — local web interface for evidence management and tailoring sessions, with a live trace of the grounding process as it runs
- **CLI** — same engine, scriptable

The entire AI stack runs on CPU: Gemma 4 4B via Ollama, BGE embeddings, BM25 + vector hybrid retrieval, cross-encoder reranking. No GPU required.

---

## Future enhancements

**Voice fine-tuning** — adapting Gemma 4's writing output to match the user's own writing voice, trained on their own documents using LoRA. Requires GPU access; planned as a follow-on phase after the first version ships.

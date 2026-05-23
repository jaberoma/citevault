# Citevault

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Grounded résumé tailoring powered by [Gemma 4](https://ai.google.dev/gemma).
> Every claim is backed by your own evidence — or refused. No fabrication.**

Most AI résumé tools invent skills you don't have. Citevault does the opposite: it only writes a claim if it can cite the exact source span in your evidence. If it can't ground it, it refuses and reports the gap.

Runs entirely on your machine — no data leaves, no API keys required.

## How it works

1. **Upload** your evidence (CVs, LinkedIn exports, project write-ups — `.md`, `.txt`, `.pdf`) via the web UI
2. **Paste** a job posting and start a tailoring run
3. Watch requirements being grounded in real time via SSE stream
4. **Output:** tailored résumé (Markdown + downloadable PDF), cover letter, gap report — all with source citations

## Hero feature: Naive Comparison Mode

Toggle **"Compare with naive AI"** to get a side-by-side of what a generic LLM would write vs. what Citevault produces. Generic AI invents skills; Citevault refuses and gap-reports them. The difference is visible in a single screenshot.

## AI stack

| Component | Role |
|-----------|------|
| **Gemma 4 E4B** (`gemma4:e4b`) | Claim drafting, rewriting, verification — all local |
| **BGE-small-en-v1.5** | Dense embeddings for semantic retrieval |
| **BGE cross-encoder** | Re-ranking retrieved candidates before generation |
| **BM25 + SQLite FTS5** | Keyword retrieval (hybrid RAG) |
| **SQLite-vec** | Vector store — no external DB needed |

## Quick Start

**Prerequisites:** Docker + Docker Compose. No GPU required; 8 GB RAM recommended.

```bash
# 1. Start Ollama and pull the model (one-time, ~1.5 GB)
docker compose up -d ollama
docker compose exec ollama ollama pull gemma4:e4b

# 2. Start remaining services (API + UI)
docker compose up -d

# 3. Open http://localhost:5173/admin in your browser
```

From the UI:
- **Admin** — upload evidence files
- **New Tailoring** — paste a job posting and run
- **History** — review past runs and their citations
- **Settings** — switch model variant

See [docs/smoke/smoke-test.md](docs/smoke/smoke-test.md) for a full API + UI walkthrough.
See [docs/evidence-format.md](docs/evidence-format.md) for how to structure your evidence files.

## Project structure

```
citevault-api/
  src/citevault/
    domain/          # Pure business logic: claims, verification, gap reporting
    application/     # Use cases: TailorResume, IndexEvidence, EvalGoldenSet
    adapters/
      inbound/       # CLI (index/tailor/eval/serve) + FastAPI (REST + SSE)
      outbound/      # Ollama, SQLite, BGE, vector search
citevault-ui/           # React 19 + TypeScript + Vite + Tailwind (served via nginx)
golden/              # Golden eval cases
docker-compose.yml   # Three-service stack: citevault-api, citevault-ui, ollama
docs/
  inception.md                # Project background and scope
  architecture.md             # System diagram
  evidence-format.md          # How to structure evidence files
  smoke/smoke-test.md         # Step-by-step API + UI walkthrough
```

## Local development

```bash
# Backend
cd citevault-api
uv sync --extra dev
uv run pytest        # unit + integration tests
uv run mypy src/citevault/domain  # strict type checking (domain layer only)

# Frontend
cd citevault-ui
npm install
npm run dev          # dev server at http://localhost:5173

# Playwright UI tests (requires docker compose stack running)
cd citevault-ui
npx playwright install chromium
npx playwright test
```

## Project status

| Component | Notes |
|-----------|-------|
| **Engine + CLI** | Complete |
| **Eval Framework** | Golden eval set (5 cases) — run `uv run citevault eval --golden golden` to measure |
| **React UI** | SSE streaming, Naive Comparison Mode, Playwright tests |
| **Voice Fine-tune** | In development — LoRA on Gemma 4B to match user writing voice |

## Maintenance

This project is provided **as-is** under the [MIT License](LICENSE), with no warranty or
guarantee of support. It is maintained by a single developer on a best-effort basis —
issues and pull requests are welcome, but there is no SLA on responses or updates.
See [CONTRIBUTING.md](CONTRIBUTING.md) for how to report bugs or submit changes.

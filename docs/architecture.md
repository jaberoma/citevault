# Citevault — Architecture

---

## Stack overview

Full three-service Docker Compose stack: Ollama + FastAPI + React UI (nginx).
Also includes the CLI and eval framework.

```
┌──────────────────────────────────────────────────────────────────┐
│  Docker Compose stack  (docker compose up)                      │
│                                                                  │
│   Browser                                                        │
│      │  HTTP :5173                                               │
│      ▼                                                           │
│   ┌──────────────────┐                                           │
│   │   citevault-ui      │  React 19 + TypeScript + Vite             │
│   │   nginx:1.27     │  served as static SPA                     │
│   │   port 5173→80   │  SSE-aware proxy config                   │
│   └────────┬─────────┘                                           │
│            │  HTTP :8000  (proxied /api/* → citevault-api)          │
│            ▼                                                      │
│   ┌──────────────────┐                                           │
│   │   citevault-api     │  FastAPI + uvicorn                        │
│   │   port 8000      │  Container built once at startup          │
│   │   hexagonal      │  (FastAPI lifespan singleton pattern)      │
│   └────────┬─────────┘                                           │
│            │  HTTP :11434                                         │
│            ▼                                                      │
│   ┌──────────────────┐                                           │
│   │   ollama         │  gemma4:e4b                               │
│   │   port 11434     │  CPU inference (~3–8 tok/s on 4-core CPU) │
│   └──────────────────┘                                           │
│                                                                  │
│   Volumes:                                                       │
│     citevault-data      → /data/citevault.db  (SQLite)                │
│     citevault-shared-ollama-data  → persistent Ollama model store  │
│     ./evidence → /evidence:ro                                    │
│     ./out      → /out                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## React UI structure (citevault-ui)

```
src/
├── api/
│   ├── client.ts      → typed wrappers for all REST + SSE endpoints
│   └── types.ts       → shared TypeScript types
├── components/
│   ├── VerdictBadge.tsx       → VERIFIED / REWRITTEN / REJECTED chips
│   ├── DiffViewer.tsx         → side-by-side grounded vs naive AI
│   ├── ClaimWithCitations.tsx → claim bubble with inline citation markers
│   ├── DropZone.tsx           → drag-and-drop file upload
│   └── SourceSpanPopover.tsx  → popover showing cited evidence span
└── pages/
    ├── admin/
    │   ├── EvidenceLibrary.tsx  → upload / list / delete sources
    │   ├── Settings.tsx         → model selection, config
    │   └── SourceInspector.tsx  → view indexed spans for a source
    └── tailor/
        ├── NewTailoring.tsx     → job posting textarea, submit
        ├── TailoringView.tsx    → SSE live trace + tabs
        │   tabs: Résumé | Cover Letter | Naive AI | Diff
        └── History.tsx          → list past tailorings
```

---

## HTTP API surface (citevault-api)

```
GET  /api/evidence                        → list sources
POST /api/evidence/source                 → upload file (multipart)
GET  /api/evidence/source/{id}            → get source detail
DELETE /api/evidence/source/{id}          → delete + cascade spans

POST /api/tailor                          → start tailoring job (async)
GET  /api/tailor/{id}                     → get result (poll)
GET  /api/tailor/{id}/stream              → SSE live trace
GET  /api/tailor/{id}/pdf                 → download résumé PDF
GET  /api/tailor                          → list past tailorings

GET  /api/settings                        → get AppSettings { model, available }
PUT  /api/settings                        → update AppSettings (validates model in Ollama)
GET  /api/ollama/models                   → list available Ollama models
GET  /api/health                          → liveness / readiness probe
```

---

## SSE live trace flow

```
UI: POST /api/tailor  → { tailoring_id }
UI: GET /api/tailor/{id}  ← initial poll; skips stream if already complete/error
UI: new EventSource(/api/tailor/{id}/stream)

citevault-api:
  background thread runs _run_tailoring()
    → { event: "started",             data: { tailoring_id } }
    → { event: "posting_parsed",      data: { requirements_count } }
    → { event: "requirement_started", data: { req_id, text } }
    → { event: "retrieval_done",      data: { req_id, candidate_count } }
    → { event: "claim_finalized",     data: { claim_id, status, text, verdict } }
    → { event: "complete",            data: { tailoring_id } }
    → { event: "error",               data: { message } }  ← on failure

UI on "complete":
  → calls GET /api/tailor/{id}  ← fetches full result (NOT from event data)
  → renders résumé, cover letter, gap report, naive comparison
```

---

## Naive Comparison Mode

```
POST /api/tailor  { "job_posting": "...", "naive_compare": true }

Pipeline runs normally → grounded résumé
THEN: LLM called with generous, unconstrained prompt → naive_md
Result: { ..., "naive_md": "..." }

UI: renders DiffViewer with grounded (left) vs naive AI (right)
    VerdictBadge on each bullet: VERIFIED / REWRITTEN / REJECTED
```

---

## FastAPI lifespan singleton

```python
# Container built ONCE at startup — not per-request
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "container"):   # guard lets tests pre-set mock
        app.state.container = Container(ContainerConfig(
            db_path=..., ollama_base_url=..., ollama_model=..., ollama_timeout_s=...,
        ))                                     # loads BGE models ONCE
    yield

# All route handlers read:
container = request.app.state.container
```

---

## Eval framework (CLI)

Runs all golden cases through the full pipeline via `GoldenCaseRunner` (`application/run_evals.py`):

```bash
cd citevault-api
uv run citevault eval --golden ../golden
```

---

## Voice fine-tune pipeline (finetune/)

Independent `uv` project — does not touch `citevault-api`.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Fine-tune pipeline  (one-shot CLI)                                     │
│                                                                          │
│  Step 1 — Dataset builder                                                │
│    voice-samples/*.md   →  OllamaSyntheticPromptLLM                     │
│                         →  list[TrainingPair(prompt, response)]          │
│    filter: ≥ 100 words per sample                                        │
│    Ollama model used: gemma4:e4b (generates the synthetic prompt)        │
│                                                                          │
│  Step 2 — LoRA trainer                                                   │
│    base model: google/gemma-4-4b-it  (HuggingFace)                     │
│    library: peft + transformers + accelerate                             │
│    config: rank=16, alpha=32, target=q_proj+v_proj, epochs=2             │
│    output: out/adapter/  (adapter_config.json + pytorch weights)         │
│                                                                          │
│  Step 3 — GGUF exporter                                                 │
│    requires: LLAMA_CPP_DIR env var (llama.cpp cloned+built by user)     │
│    shells out to: convert_lora_to_gguf.py                               │
│    output: out/citevault-voice.gguf + out/Modelfile                     │
│                                                                          │
│  User registers model:                                                   │
│    cd out && ollama create citevault-voice -f ./Modelfile               │
│                                                                          │
│  Citevault Settings → Model → pick "citevault-voice"                    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Voice fine-tune quality gate (two axes)

```
┌─────────────────────────────────────────────────────┐
│  Before adopting citevault-voice, verify both:      │
│                                                     │
│  Axis 1 — Voice fidelity                            │
│    OllamaJudge (pairwise LLM-as-judge)              │
│    Reference writing vs fine-tuned vs base          │
│    Gate: win rate ≥ 65%                             │
│                                                     │
│  Axis 2 — Grounding regression                      │
│    Re-run golden eval with citevault-voice          │
│    Compare First-Pass Grounding Rate vs baseline    │
│    Gate: regression ≤ 3 percentage points           │
└─────────────────────────────────────────────────────┘
```

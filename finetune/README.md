# Citevault Voice Fine-Tune

Adapt Gemma (`gemma4:e4b`) to write in your voice via LoRA. CLI-only, batch operation.
Takes hours on a modern laptop; minutes on a beefy GPU.

## Preparing voice samples

Place writing samples in `./voice-samples/` as `.md` or `.txt` files. Each file
must be ≥ 100 words. Good source types:
- Past cover letters
- Blog posts
- Long-form professional emails
- Op-eds, essays, README intros

Aim for 100–300 samples, 50k–100k total tokens.

## Prerequisites

- Ollama running with `gemma4:e4b` pulled (used to generate synthetic prompts
  for training pairs and for the voice-fidelity judge)
- `llama.cpp` cloned and built, with its directory exported as `LLAMA_CPP_DIR`
- ~10 GB free disk space; ~16 GB VRAM (or unified memory on Apple Silicon)
  recommended for the training step

If you don't have `llama.cpp` available, use `--skip-export` to run the
dataset-building and training steps only (GGUF export is skipped):

```bash
uv run python -m citevault_finetune --voice ./voice-samples/ --out ./out --skip-export
```

## Run

```bash
cd finetune
uv sync --extra dev
uv run python -m citevault_finetune --voice ./voice-samples/ --out ./out
```

## Tests

Unit tests (no dependencies required):

```bash
.venv/bin/pytest
```

Integration tests against a live Ollama instance (dataset builder + voice evaluator):

```bash
CITEVAULT_FINETUNE_INTEGRATION=1 .venv/bin/pytest tests/test_integration.py -v
```

Trainer smoke test (downloads ~10 MB of tiny-gpt2, CPU-only):

```bash
CITEVAULT_FINETUNE_SMOKE=1 .venv/bin/pytest tests/test_trainer_smoke.py -v
```

## Register the model with Ollama

After the run completes:

```bash
cd out
ollama create citevault-voice -f ./Modelfile
```

## Use in Citevault

Open the Citevault UI → **Admin → Settings → Model**, pick `citevault-voice`, save.

## Evaluation before adopting

We strongly recommend running both quality gates before switching:

```bash
# Verify grounding hasn't regressed vs baseline
CITEVAULT_MODEL=citevault-voice \
  uv run --project ../citevault-api citevault eval --golden ../golden

# Voice judge: aim for fine-tuned wins ≥ 65% of pairwise comparisons.
# See finetune/src/citevault_finetune/voice_evaluator.py for the OllamaJudge.
```

If grounding regresses more than 3 percentage points, retrain with a lower
learning rate (`--lr 5e-5`) or fewer epochs (`--epochs 1`).

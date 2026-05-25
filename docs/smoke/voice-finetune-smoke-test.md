# Voice Fine-Tune Smoke Test

**Prerequisites:** Ollama running with `gemma4:e4b` pulled (for dataset builder + voice judge).
GGUF export additionally requires `LLAMA_CPP_DIR` — see step 4.

---

## 1. Unit tests (no Ollama, no GPU — runs in seconds)

```bash
cd /path/to/citevault/finetune
uv sync --extra dev
.venv/bin/pytest tests/ -v --ignore=tests/test_trainer_smoke.py
```

**Expected:** `14 passed`

```
tests/test_adapter_exporter.py::test_write_modelfile PASSED
tests/test_adapter_exporter.py::test_write_modelfile_includes_temperature PASSED
tests/test_adapter_exporter.py::test_export_calls_llama_cpp_converter PASSED
tests/test_adapter_exporter.py::test_export_raises_without_llama_cpp_dir PASSED
tests/test_dataset_builder.py::test_filter_rejects_short_samples PASSED
tests/test_dataset_builder.py::test_build_dataset_pairs_prompts_with_writing PASSED
tests/test_dataset_builder.py::test_build_dataset_skips_non_text_files PASSED
tests/test_grounding_check.py::test_regression_within_tolerance_passes PASSED
tests/test_grounding_check.py::test_regression_outside_tolerance_fails PASSED
tests/test_grounding_check.py::test_regression_exact_boundary_passes PASSED
tests/test_grounding_check.py::test_regression_improvement_passes PASSED
tests/test_voice_evaluator.py::test_evaluator_returns_pairwise_win_rate PASSED
tests/test_voice_evaluator.py::test_evaluator_handles_mixed_results PASSED
tests/test_voice_evaluator.py::test_evaluator_empty_input_returns_zero PASSED
```

---

## 2. LoRA training smoke (tiny-gpt2, no GPU needed, ~30 seconds)

Downloads `sshleifer/tiny-gpt2` (~10 MB) on first run.

```bash
cd /path/to/citevault/finetune
CITEVAULT_FINETUNE_SMOKE=1 .venv/bin/pytest tests/test_trainer_smoke.py -v -s
```

**Expected:**
```
tests/test_trainer_smoke.py::test_one_step_lora_training PASSED
```

And `out/adapter/adapter_config.json` created in a temp dir.

**Note:** This test uses `tiny-gpt2`, not Gemma — it only validates the LoRA wiring, not model quality.

---

## 3. Dataset builder with real Ollama

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull gemma4:e4b  # if not already pulled

# Create some fake voice samples
mkdir -p /tmp/voice-test
for i in 1 2 3; do
  python3 -c "print(' '.join(['The' if j%10==0 else 'engineering' for j in range(200)]))" \
    > /tmp/voice-test/sample_$i.md
done

cd /path/to/citevault/finetune
OLLAMA_HOST=http://localhost:11434 .venv/bin/python - <<'EOF'
from citevault_finetune.dataset_builder import DatasetBuilder, OllamaSyntheticPromptLLM
builder = DatasetBuilder(llm=OllamaSyntheticPromptLLM())
pairs = builder.build("/tmp/voice-test")
print(f"Built {len(pairs)} pairs")
for p in pairs:
    print(f"  prompt: {p.prompt[:60]}...")
EOF
```

**Expected:** `Built 3 pairs` with non-empty prompts.

**Note:** Each call takes 10–60 seconds on CPU. Total ~1–3 minutes for 3 samples.

---

## 4. Modelfile writer

```bash
mkdir -p /tmp/cv-out
cd /path/to/citevault/finetune
.venv/bin/python - <<'EOF'
from citevault_finetune.adapter_exporter import write_ollama_modelfile
write_ollama_modelfile(
    out_path="/tmp/cv-out/Modelfile",
    base_tag="gemma4:e4b",
    adapter_gguf="./citevault-voice.gguf",
)
print(open("/tmp/cv-out/Modelfile").read())
EOF
```

**Expected:**
```
FROM gemma4:e4b
ADAPTER ./citevault-voice.gguf
PARAMETER temperature 0.4
```

---

## 5. GGUF export (requires llama.cpp — user must build)

This step **cannot be automated** without `LLAMA_CPP_DIR`. Build once:

```bash
git clone https://github.com/ggerganov/llama.cpp /opt/llama.cpp
cd /opt/llama.cpp && cmake -B build && cmake --build build --config Release -j$(nproc)
export LLAMA_CPP_DIR=/opt/llama.cpp
```

Then, with a real trained adapter in `./out/adapter/`:

```bash
cd /path/to/citevault/finetune
LLAMA_CPP_DIR=/opt/llama.cpp .venv/bin/python -m citevault_finetune \
  --skip-train \
  --voice ./voice-samples \
  --out ./out
```

**Expected:**
```
[3/3] Exporting to GGUF + Modelfile…
Done! Next step:
  cd ./out && ollama create citevault-voice -f ./Modelfile
```

---

## 6. Grounding regression check

Compare First-Pass Grounding Rate before and after fine-tune:

```bash
cd /path/to/citevault/finetune
.venv/bin/python - <<'EOF'
from citevault_finetune.grounding_check import check_regression

# Replace with your actual measured values
result = check_regression(before_rate=0.78, after_rate=0.75, tolerance_pct=3.0)
print(result.message)
print("PASSED" if result.passed else "FAILED")
EOF
```

**Expected (example with 3pp drop):**
```
First-Pass Grounding 78.0% → 75.0% (-3.0pp). within tolerance (3.0pp).
PASSED
```

---

## 7. Full CLI dry-run (structure check, no Ollama)

```bash
cd /path/to/citevault/finetune
.venv/bin/python -m citevault_finetune --help
```

**Expected:** argparse help showing `--voice`, `--out`, `--rank`, `--alpha`, `--epochs`, `--lr`, `--base-model`, `--base-ollama-tag`, `--skip-train`.

---

## Hardware note

Running the real LoRA fine-tune on a CPU-only laptop is not practical for Gemma 4B.
Cloud options:

| Option | Notes |
|--------|-------|
| Google Colab (free tier) | T4 GPU, ~2–4 hours for 2 epochs on 100 samples |
| Colab Pro | A100, ~20–30 minutes |
| Vast.ai / RunPod | RTX 4090, ~15 minutes |
| Apple M-series Mac | MPS backend, ~1 hour on M2 Pro |

The smoke test (step 2) using `tiny-gpt2` is the only training step runnable locally.

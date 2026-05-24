# Hardware & Performance Notes

Measured on the development machine. Read before running any smoke test.

---

## Machine specs

| Component | Value |
|-----------|-------|
| CPU | 4-core / 8-thread laptop CPU (no discrete GPU) |
| RAM | 32 GB |
| GPU | integrated graphics — **not supported by Ollama** |
| Inference backend | CPU only |

---

## Gemma 4 4B (gemma4:e4b) performance

| Metric | Value |
|--------|-------|
| Quantization | Q4_K_M (already the default tag) |
| Model size on disk | ~2.5 GB |
| Tokens / second (CPU) | 3–8 tok/s |
| Typical single LLM call (200–400 tokens output) | 30–120 seconds |
| Full tailoring run (6–10 LLM calls) | 4–15 minutes |
| Full eval run (5 cases × ~8 calls each) | 40–120 minutes |

**Expectation:** Citevault works correctly on this machine but is not "fluent" speed-wise. Plan for long waits during smoke tests.

---

## Optimization knobs

These are the levers available without hardware changes:

### 1. Set Ollama thread count (most impactful)

By default Ollama may not use all cores. Force all 8 threads:

```bash
# In docker-compose.yml, under the ollama service:
environment:
  - OLLAMA_NUM_THREADS=8

# Or for a local Ollama process:
OLLAMA_NUM_THREADS=8 ollama serve
```

This alone can improve throughput by 20–40%.

### 2. Reduce context window

The engine already uses targeted prompts. If you customize prompts, keep them short.

### 3. Batch where possible

The BGE reranker already batches all candidates in one forward pass. The embedding model also batches. These are already optimal.

### 4. Container singleton

The FastAPI lifespan pattern ensures BGE models load once at startup, not per-request. This eliminates the 5–30 second model-load penalty on each API call.

---

## What is NOT achievable on this hardware

- Real-time / sub-second LLM responses
- LoRA fine-tuning on Gemma 4B (requires GPU with ≥16 GB VRAM)
- Parallel inference (Ollama queues requests)

---

## iGPU note

Ollama does not support OpenCL or Vulkan for inference. There is no gain from integrated graphics for this workload.

`llama.cpp` supports Vulkan, but getting it working with Ollama's internal llama.cpp build requires a custom Ollama build — not recommended for a contest submission.

---

## Cloud alternatives for voice fine-tuning

If you want to actually run the LoRA pipeline on Gemma 4B:

| Platform | GPU | Estimated time (2 epochs, 100 samples) | Cost |
|----------|-----|----------------------------------------|------|
| Google Colab Free | T4 (16 GB) | 2–4 hours | Free |
| Google Colab Pro | A100 (40 GB) | 20–30 min | ~$10/month |
| Vast.ai | RTX 4090 (24 GB) | 15–20 min | ~$0.50/hr |
| RunPod | RTX 3090 (24 GB) | 20–30 min | ~$0.40/hr |
| Apple M2 Pro | MPS (32 GB unified) | ~60 min | (own hardware) |

Minimum VRAM for QLoRA (4-bit base) on Gemma 4B: 8 GB.

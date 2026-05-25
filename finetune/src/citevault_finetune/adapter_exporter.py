"""Convert a saved LoRA adapter to GGUF and emit an Ollama Modelfile."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def write_ollama_modelfile(
    out_path: str,
    base_tag: str = "gemma4:e4b",
    adapter_gguf: str = "./voice.gguf",
) -> None:
    Path(out_path).write_text(
        f"FROM {base_tag}\n"
        f"ADAPTER {adapter_gguf}\n"
        "PARAMETER temperature 0.4\n"
    )


def export_lora_to_gguf(adapter_dir: str, out_gguf: str) -> None:
    """Shell out to llama.cpp's convert_lora_to_gguf.py."""
    llama_cpp = os.environ.get("LLAMA_CPP_DIR")
    if not llama_cpp:
        raise RuntimeError(
            "LLAMA_CPP_DIR is not set. Clone https://github.com/ggerganov/llama.cpp "
            "and export LLAMA_CPP_DIR=/path/to/llama.cpp before running the export."
        )
    script = Path(llama_cpp) / "convert_lora_to_gguf.py"
    cmd = ["python", str(script), "--outfile", out_gguf, adapter_dir]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"llama.cpp conversion failed: exit {result.returncode}")

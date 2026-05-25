"""Entry point for `python -m citevault_finetune`."""

from __future__ import annotations

import argparse
from pathlib import Path

from citevault_finetune.adapter_exporter import export_lora_to_gguf, write_ollama_modelfile
from citevault_finetune.dataset_builder import DatasetBuilder, OllamaSyntheticPromptLLM
from citevault_finetune.trainer import LoraTrainer, TrainConfig


def main() -> None:
    p = argparse.ArgumentParser(prog="citevault_finetune")
    p.add_argument("--voice", required=True, help="Folder with user writing samples.")
    p.add_argument("--out", default="./out", help="Where to write the adapter + Modelfile.")
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--base-model", default="google/gemma-4-4b-it")
    p.add_argument("--base-ollama-tag", default="gemma4:e4b")
    p.add_argument(
        "--skip-train",
        action="store_true",
        help="Skip training (assume adapter already in --out/adapter).",
    )
    args = p.parse_args()

    out_dir = Path(args.out)
    adapter_dir = out_dir / "adapter"
    gguf_path = out_dir / "citevault-voice.gguf"
    modelfile = out_dir / "Modelfile"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_train:
        print("[1/3] Building dataset from voice samples…")
        builder = DatasetBuilder(llm=OllamaSyntheticPromptLLM())
        pairs = builder.build(args.voice)
        if not pairs:
            raise SystemExit(
                "No usable voice samples found (need ≥100 words per file)."
            )
        print(f"  → {len(pairs)} (prompt, response) pairs.")

        print("[2/3] Training LoRA adapter…")
        cfg = TrainConfig(
            base_model=args.base_model,
            out_dir=str(adapter_dir),
            rank=args.rank,
            alpha=args.alpha,
            epochs=args.epochs,
            lr=args.lr,
        )
        LoraTrainer(cfg).train(pairs)
        print(f"  → adapter saved to {adapter_dir}")
    else:
        print("[1-2/3] Skipped training; using existing adapter.")

    print("[3/3] Exporting to GGUF + Modelfile…")
    export_lora_to_gguf(adapter_dir=str(adapter_dir), out_gguf=str(gguf_path))
    write_ollama_modelfile(
        out_path=str(modelfile),
        base_tag=args.base_ollama_tag,
        adapter_gguf=str(gguf_path.name),
    )
    print("\nDone! Next step:")
    print(f"  cd {out_dir} && ollama create citevault-voice -f ./Modelfile")
    print("Then open Citevault Settings → Model and pick 'citevault-voice'.")


if __name__ == "__main__":
    main()

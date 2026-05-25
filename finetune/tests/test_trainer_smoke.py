"""LoRA trainer smoke test — skipped by default; opt-in with CITEVAULT_FINETUNE_SMOKE=1.

Runs a 1-step training pass on a tiny base model just to verify the pipeline wires.
DO NOT run unattended; downloads ~10 MB on first invocation.
"""

import os
from pathlib import Path

import pytest

from citevault_finetune.dataset_builder import TrainingPair


@pytest.mark.skipif(
    os.environ.get("CITEVAULT_FINETUNE_SMOKE") != "1",
    reason="Heavy smoke; opt in with CITEVAULT_FINETUNE_SMOKE=1.",
)
def test_one_step_lora_training(tmp_path: Path) -> None:
    from citevault_finetune.trainer import LoraTrainer, TrainConfig

    pairs = [TrainingPair(prompt=f"Prompt {i}", response=f"Response {i} " * 20)
             for i in range(4)]
    cfg = TrainConfig(
        base_model="sshleifer/tiny-gpt2",
        out_dir=str(tmp_path / "adapter"),
        rank=4, alpha=8, epochs=1, lr=1e-4, max_steps=1,
        target_modules=["c_attn"],  # GPT-2 uses c_attn, not q_proj/v_proj
    )
    LoraTrainer(cfg).train(pairs)
    assert (Path(cfg.out_dir) / "adapter_config.json").exists()

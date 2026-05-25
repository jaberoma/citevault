"""LoRA training pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from citevault_finetune.dataset_builder import TrainingPair


@dataclass
class TrainConfig:
    base_model: str = "google/gemma-4-4b-it"
    out_dir: str = "./out/adapter"
    rank: int = 16
    alpha: int = 32
    epochs: int = 2
    lr: float = 1e-4
    max_steps: int | None = None
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    # Attention module names vary by architecture: q_proj/v_proj (Gemma/Llama),
    # c_attn (GPT-2). Override for non-Gemma base models.
    target_modules: list[str] = field(default_factory=lambda: ["q_proj", "v_proj"])


class LoraTrainer:
    def __init__(self, cfg: TrainConfig) -> None:
        self.cfg = cfg

    def train(self, pairs: list[TrainingPair]) -> None:
        # Heavy imports kept inside .train so test collection doesn't load them.
        import os
        import torch
        from datasets import Dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )

        os.makedirs(self.cfg.out_dir, exist_ok=True)
        tok = AutoTokenizer.from_pretrained(self.cfg.base_model, use_fast=True)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token

        def fmt(p: TrainingPair) -> str:
            return f"### Instruction:\n{p.prompt}\n\n### Response:\n{p.response}"

        ds = Dataset.from_list([{"text": fmt(p)} for p in pairs])

        def tokenize(batch: dict[str, Any]) -> dict[str, Any]:
            return tok(batch["text"], truncation=True, max_length=2048)

        ds = ds.map(tokenize, batched=True, remove_columns=["text"])

        model = AutoModelForCausalLM.from_pretrained(
            self.cfg.base_model,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        lora_cfg = LoraConfig(
            r=self.cfg.rank,
            lora_alpha=self.cfg.alpha,
            target_modules=self.cfg.target_modules,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_cfg)

        args = TrainingArguments(
            output_dir=self.cfg.out_dir,
            num_train_epochs=self.cfg.epochs,
            per_device_train_batch_size=self.cfg.batch_size,
            gradient_accumulation_steps=self.cfg.gradient_accumulation_steps,
            learning_rate=self.cfg.lr,
            lr_scheduler_type="cosine",
            logging_steps=10,
            save_strategy="epoch",
            max_steps=self.cfg.max_steps or -1,
            report_to=[],
        )
        collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)
        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=ds,
            data_collator=collator,
        )
        trainer.train()
        model.save_pretrained(self.cfg.out_dir)
        tok.save_pretrained(self.cfg.out_dir)

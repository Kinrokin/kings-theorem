import argparse

import yaml
from datasets import load_dataset
from transformers import TrainingArguments
from trl import DPOTrainer
from unsloth import FastLanguageModel, PatchDPOTrainer, is_bfloat16_supported

PatchDPOTrainer()


def load_cfg(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main(config_path):
    cfg = load_cfg(config_path)
    print(f"🔥 DPO Ignition: {cfg['model_name']}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=cfg["model_name"],
        max_seq_length=cfg["max_seq_length"],
        dtype=None,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg["lora_r"],
        target_modules=cfg["target_modules"],
        lora_alpha=cfg["lora_alpha"],
        lora_dropout=0,  # DPO suggests 0 dropout
        bias="none",
        task_type="CAUSAL_LM",
    )
    dataset = load_dataset("json", data_files=cfg["dataset_path"], split="train")
    training_args = TrainingArguments(
        output_dir=cfg["output_dir"],
        num_train_epochs=1,
        per_device_train_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=cfg["grad_accum"],
        learning_rate=5e-6,  # Lower LR for DPO
        beta=0.1,  # DPO beta
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        optim="adamw_8bit",
        save_strategy="epoch",
    )
    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # Unsloth handles ref_model implicitly efficiently
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        beta=0.1,
        max_prompt_length=1024,
        max_length=cfg["max_seq_length"],
    )
    print("🚀 Starting Unsloth DPO...")
    trainer.train()
    print(f"✅ DPO Complete. Saving to {cfg['output_dir']}")
    model.save_pretrained(cfg["output_dir"])
    tokenizer.save_pretrained(cfg["output_dir"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/dpo_config.yaml")
    args = parser.parse_args()
    main(args.config)

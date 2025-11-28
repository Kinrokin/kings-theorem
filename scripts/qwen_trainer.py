#!/usr/bin/env python3
"""
Qwen3 8B QLoRA Trainer - For Colab/Cloud GPU

Fine-tunes Qwen3 8B with QLoRA (bitsandbytes) on teacher (silver medal) data.

**This script is designed to run on Colab with GPU, not on local CPU.**

Usage (on Colab):
  python scripts/qwen_trainer.py \\
    --input data/teacher/silver_medal_job123.jsonl \\
    --output-dir models/qwen3-finetuned-job123 \\
    --epochs 3 \\
    --batch-size 4

Requirements:
  - GPU (T4, A100, etc.)
  - transformers
  - datasets
  - bitsandbytes
  - peft
  - accelerate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
    )
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install transformers datasets peft bitsandbytes accelerate torch")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # or local path
MAX_LENGTH = 2048


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file into list of dicts."""
    data = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def prepare_dataset(jsonl_path: Path, tokenizer: Any) -> Dataset:
    """
    Prepare Hugging Face Dataset from JSONL.
    
    Expects fields:
      - instruction
      - response_compressed (target output)
    
    Args:
        jsonl_path: Path to silver medal JSONL
        tokenizer: Qwen tokenizer
        
    Returns:
        Hugging Face Dataset
    """
    data = load_jsonl(jsonl_path)
    
    formatted = []
    for entry in data:
        instruction = entry.get("instruction", "")
        target = entry.get("response_compressed", "") or entry.get("response", "")
        
        if not instruction or not target:
            continue
        
        # Format as chat (Qwen template)
        prompt = f"<|im_start|>user\n{instruction}<|im_end|>\n<|im_start|>assistant\n"
        full_text = prompt + target + "<|im_end|>"
        
        # Tokenize
        tokens = tokenizer(
            full_text,
            truncation=True,
            max_length=MAX_LENGTH,
            padding=False,
        )
        
        formatted.append({
            "input_ids": tokens["input_ids"],
            "attention_mask": tokens["attention_mask"],
            "labels": tokens["input_ids"],  # Causal LM loss
        })
    
    return Dataset.from_list(formatted)


# ═══════════════════════════════════════════════════════════════════════════
# TRAINING
# ═══════════════════════════════════════════════════════════════════════════


def train_qwen(
    input_path: Path,
    output_dir: Path,
    model_name: str = DEFAULT_MODEL,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    lora_r: int = 8,
    lora_alpha: int = 16,
    verbose: bool = True,
) -> None:
    """
    Fine-tune Qwen3 8B with QLoRA.
    
    Args:
        input_path: Path to silver medal JSONL
        output_dir: Directory to save trained model/adapter
        model_name: Hugging Face model ID or local path
        epochs: Number of training epochs
        batch_size: Per-device batch size
        learning_rate: Learning rate
        lora_r: LoRA rank
        lora_alpha: LoRA alpha
        verbose: Enable logging
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"🐉 QWEN3 8B QLORA TRAINER")
        print(f"{'='*70}")
        print(f"Input: {input_path}")
        print(f"Output: {output_dir}")
        print(f"Model: {model_name}")
        print(f"Epochs: {epochs}, Batch: {batch_size}, LR: {learning_rate}")
        print(f"LoRA: r={lora_r}, alpha={lora_alpha}")
        print(f"{'='*70}\n")
    
    # Check GPU
    if not torch.cuda.is_available():
        print("⚠️  WARNING: No GPU detected. Training will be extremely slow.")
        print("   This script is designed for Colab with GPU.")
    
    # Load tokenizer
    if verbose:
        print("📥 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    # Load model with 4-bit quantization
    if verbose:
        print("📥 Loading model with 4-bit quantization...")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        load_in_4bit=True,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # LoRA config
    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    model = get_peft_model(model, lora_config)
    
    if verbose:
        print(f"✅ Model loaded with LoRA adapters")
        model.print_trainable_parameters()
    
    # Prepare dataset
    if verbose:
        print(f"\n📊 Preparing dataset from {input_path}...")
    dataset = prepare_dataset(input_path, tokenizer)
    
    if verbose:
        print(f"✅ Dataset ready: {len(dataset)} samples")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        fp16=False,
        bf16=torch.cuda.is_available(),
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        optim="adamw_8bit",
        warmup_steps=50,
        report_to="none",  # Disable wandb/tensorboard
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    
    # Train
    if verbose:
        print(f"\n🚀 Starting training...")
    
    trainer.train()
    
    # Save
    if verbose:
        print(f"\n💾 Saving model to {output_dir}...")
    
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🎉 TRAINING COMPLETE")
        print(f"{'='*70}")
        print(f"Model saved to: {output_dir}")
        print(f"\n📝 Next steps:")
        print(f"   1. Download the model from Colab")
        print(f"   2. Place it in your local models/ directory")
        print(f"   3. Update QWEN_LOCAL_PATH env var")
        print(f"{'='*70}\n")


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    """QLoRA trainer CLI."""
    parser = argparse.ArgumentParser(
        description="Qwen3 8B QLoRA Trainer - For Colab/Cloud GPU",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (on Colab):
  # Basic training
  python scripts/qwen_trainer.py \\
    --input data/teacher/silver_medal.jsonl \\
    --output-dir models/qwen3-finetuned

  # Custom hyperparameters
  python scripts/qwen_trainer.py \\
    --input data/teacher/silver_medal.jsonl \\
    --output-dir models/qwen3-custom \\
    --epochs 5 \\
    --batch-size 2 \\
    --learning-rate 3e-4 \\
    --lora-r 16

Requirements:
  - GPU (T4, A100, etc.)
  - transformers, datasets, peft, bitsandbytes, accelerate
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to silver medal JSONL file",
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save trained model/adapter",
    )
    
    parser.add_argument(
        "--model-name",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Hugging Face model ID or local path (default: {DEFAULT_MODEL})",
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Per-device batch size (default: 4)",
    )
    
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-4,
        help="Learning rate (default: 2e-4)",
    )
    
    parser.add_argument(
        "--lora-r",
        type=int,
        default=8,
        help="LoRA rank (default: 8)",
    )
    
    parser.add_argument(
        "--lora-alpha",
        type=int,
        default=16,
        help="LoRA alpha (default: 16)",
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    
    args = parser.parse_args()
    
    try:
        train_qwen(
            input_path=Path(args.input),
            output_dir=Path(args.output_dir),
            model_name=args.model_name,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            verbose=not args.quiet,
        )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

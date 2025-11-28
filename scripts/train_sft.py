"""Minimal SFT training script for King's Theorem golden dataset with
validation and metrics logging.

Loads `logs/golden_dataset.jsonl` where each line is a JSON object with
`prompt` and `completion` keys. The `completion` field itself is a JSON
string; we flatten it to a textual target.

Adds:
- Validation split
- Trainer with evaluation each epoch
- Metrics written to checkpoint dir (metrics.json)
- Metrics appended into data/system_state.json for observability

Usage:
    python scripts/train_sft.py --epochs 1 --batch-size 2 --max-samples 64
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import argparse

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

DEFAULT_DATA_FILE = Path("logs/golden_dataset.jsonl")


def load_samples(limit: int | None = None, dataset_path: Optional[str] = None) -> List[dict]:
    path = Path(dataset_path) if dataset_path else DEFAULT_DATA_FILE
    lines = path.read_text().splitlines() if path.exists() else []
    samples: List[dict] = []
    for l in lines[: limit or len(lines)]:
        try:
            rec = json.loads(l)
        except Exception:
            continue
        prompt = rec.get("prompt", "")
        completion_raw = rec.get("completion", "")
        # Flatten completion JSON for textual target
        try:
            inner = json.loads(completion_raw)
            completion_text = inner.get("rationale", "")
        except Exception:
            completion_text = completion_raw
        samples.append({"prompt": prompt, "completion": completion_text})
    return samples


@dataclass
class TrainConfig:
    model_name: str = "distilgpt2"
    epochs: int = 1
    batch_size: int = 2
    lr: float = 5e-5
    max_samples: int | None = None
    max_length: int = 256
    output_dir: str = "models/sft-distilgpt2-demo"
    val_ratio: float = 0.1
    dataset: Optional[str] = None
    no_cuda: bool = False


class TextDataset(torch.utils.data.Dataset):
    def __init__(self, samples: List[dict], tokenizer, max_length: int):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        text = s["prompt"] + "\n" + s["completion"]
        enc = self.tokenizer(
            text,
            return_tensors="pt",
            padding=False,
            truncation=True,
            max_length=self.max_length,
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        return item


def train(cfg: TrainConfig):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg.model_name).to(device)

    samples = load_samples(cfg.max_samples, dataset_path=cfg.dataset)
    if not samples:
        raise SystemExit("No samples found in golden dataset.")

    # Split into train/val
    n = len(samples)
    val_size = max(1, int(n * cfg.val_ratio)) if n > 1 else 0
    train_samples = samples
    eval_samples: List[dict] = []
    if val_size > 0 and n > 1:
        eval_samples = samples[-val_size:]
        train_samples = samples[:-val_size]

    # Build DataLoaders with manual collate producing labels
    from torch.utils.data import DataLoader

    def collate_fn(batch):
        texts = []
        for s in batch:
            # Reconstruct text from dataset items: we stored only tokenized tensors
            # Instead, access raw samples directly by index alignment
            raise RuntimeError("Internal: collate_fn expects raw samples; dataset returns tokenized.")

    # We will avoid Dataset/tokenized path and directly tokenize in collate over raw samples
    train_samples_raw = train_samples
    eval_samples_raw = eval_samples

    def collate_raw(samples):
        texts = [s["prompt"] + "\n" + s["completion"] for s in samples]
        enc = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=cfg.max_length)
        labels = enc.input_ids.clone()
        labels[enc.attention_mask == 0] = -100
        enc["labels"] = labels
        return enc

    train_loader = DataLoader(train_samples_raw, batch_size=cfg.batch_size, shuffle=True, collate_fn=collate_raw)
    eval_loader = DataLoader(eval_samples_raw, batch_size=max(1, cfg.batch_size), shuffle=False, collate_fn=collate_raw) if eval_samples_raw else None

    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    optim = torch.optim.AdamW(model.parameters(), lr=cfg.lr)
    train_loss_accum = 0.0
    train_steps = 0
    model.train()
    for epoch in range(cfg.epochs):
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch)
            loss = out.loss
            loss.backward()
            optim.step()
            optim.zero_grad()
            train_loss_accum += loss.item()
            train_steps += 1

    train_metrics = {"train_loss": (train_loss_accum / max(1, train_steps))}

    eval_metrics = {}
    if eval_loader:
        model.eval()
        eval_loss_accum = 0.0
        eval_steps = 0
        with torch.no_grad():
            for batch in eval_loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                out = model(**batch)
                eval_loss_accum += out.loss.item()
                eval_steps += 1
        eval_metrics = {"eval_loss": (eval_loss_accum / max(1, eval_steps))}

    # Save checkpoint (weights + tokenizer)
    model.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)

    # Write metrics to checkpoint dir
    metrics_path = out_dir / "metrics.json"
    import json, time
    payload = {
        "timestamp": time.time(),
        "train_metrics": train_metrics,
        "eval_metrics": eval_metrics,
        "samples": {"train": len(train_samples), "eval": len(eval_samples) if eval_loader else 0},
        "config": {
            "model": cfg.model_name,
            "epochs": cfg.epochs,
            "batch_size": cfg.batch_size,
            "lr": cfg.lr,
            "max_samples": cfg.max_samples,
            "max_length": cfg.max_length,
        },
    }
    metrics_path.write_text(json.dumps(payload, indent=2))

    # Append summary into data/system_state.json for observability
    try:
        state_path = Path("data/system_state.json")
        state = {}
        if state_path.exists():
            state = json.loads(state_path.read_text())
        trainings = state.get("training_metrics", [])
        trainings.append(
            {
                "timestamp": payload["timestamp"],
                "model": cfg.model_name,
                "epochs": cfg.epochs,
                "train_loss": train_metrics.get("train_loss"),
                "eval_loss": eval_metrics.get("eval_loss") if eval_metrics else None,
                "output_dir": str(out_dir),
            }
        )
        state["training_metrics"] = trainings
        state_path.write_text(json.dumps(state, indent=2))
    except Exception:
        pass

    print(f"Training complete. Checkpoint and metrics saved to {out_dir}")


def parse_args() -> TrainConfig:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="distilgpt2")
    ap.add_argument("--model_name", default=None, help="Alias for --model")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--max-samples", type=int, default=None)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--output-dir", type=str, default="models/sft-distilgpt2-demo")
    ap.add_argument("--val-ratio", type=float, default=0.1)
    ap.add_argument("--dataset", type=str, default=None, help="Path to JSONL dataset (prompt/completion)")
    ap.add_argument("--no-cuda", action="store_true", help="Force CPU training")
    a = ap.parse_args()
    model_name = a.model_name or a.model
    return TrainConfig(
        model_name=model_name,
        epochs=a.epochs,
        batch_size=a.batch_size,
        lr=a.lr,
        max_samples=a.max_samples,
        max_length=a.max_length,
        output_dir=a.output_dir,
        val_ratio=a.val_ratio,
        dataset=a.dataset,
        no_cuda=a.no_cuda,
    )


if __name__ == "__main__":
    cfg = parse_args()
    train(cfg)

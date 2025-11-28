"""Prometheus Metrics Server for King's Theorem Training & System State.

Exposes gauges on :9100 by reading data/system_state.json periodically.
Adds SFT training gauges to visualize adaptation in Grafana.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from prometheus_client import Gauge, start_http_server

STATE_PATH = Path("data/system_state.json")

# Core system gauges (examples; extend as needed)
epoch_g = Gauge("kt_epoch", "Current system epoch")
level_g = Gauge("kt_level", "Current system level")
violations_g = Gauge("kt_safety_violations", "Safety violations count")

# Training gauges
train_loss_g = Gauge("kt_train_loss", "Current SFT Training Loss")
eval_loss_g = Gauge("kt_eval_loss", "Current SFT Validation Loss")
train_samples_g = Gauge("kt_train_samples", "Number of training samples used")


def read_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {}


def latest_training_entry(state: Dict[str, Any]) -> Dict[str, Any] | None:
    tm = state.get("training_metrics")
    if isinstance(tm, list) and tm:
        return tm[-1]
    if isinstance(tm, dict):
        return tm
    return None


def update_metrics() -> None:
    state = read_state()
    if not state:
        return

    # Core
    epoch_g.set(state.get("epoch", 0))
    level_g.set(state.get("level", 0))
    violations_g.set(state.get("safety_violations", 0))

    # Training
    entry = latest_training_entry(state)
    if entry:
        # If metrics were appended by train_sft, train_loss/eval_loss present
        if "train_loss" in entry:
            try:
                train_loss_g.set(float(entry.get("train_loss", 0)))
            except Exception:
                pass
        if "eval_loss" in entry and entry.get("eval_loss") is not None:
            try:
                eval_loss_g.set(float(entry.get("eval_loss", 0)))
            except Exception:
                pass

        # If we also saved samples in metrics.json and echoed into system_state later,
        # look for nested samples
        samples = entry.get("samples")
        if isinstance(samples, dict) and "train" in samples:
            try:
                train_samples_g.set(int(samples.get("train", 0)))
            except Exception:
                pass


def main() -> None:
    start_http_server(9100)
    print("📈 Metrics Server running on :9100")
    while True:
        update_metrics()
        time.sleep(5)


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from src.utils.crypto import verify_signature


@dataclass
class RiskBudget:
    version: int
    catastrophic_max: float
    high_max: float
    medium_max: float
    min_samples: int
    last_approved_by: str | None = None


def load_risk_budget(config_path: str | Path = "config/risk_budget.yml") -> Optional[RiskBudget]:
    p = Path(config_path)
    if not p.exists():
        return None
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    rb = RiskBudget(
        version=int(data.get("version", 1)),
        catastrophic_max=float(data["catastrophic_max"]),
        high_max=float(data.get("high_max", 0.08)),
        medium_max=float(data.get("medium_max", 0.2)),
        min_samples=int(data.get("min_samples", 512)),
        last_approved_by=data.get("last_approved_by"),
    )

    # Optional signature verification, enabled by env to avoid breaking dev
    if os.getenv("KT_VERIFY_RISK_BUDGET", "0") == "1":
        sig_path = p.with_suffix(p.suffix + ".sig")
        pub_key = os.getenv("KT_OPERATOR_PUB", str(Path("keys/operator.pub").resolve()))
        if not sig_path.exists():
            raise RuntimeError(f"Risk budget signature missing: {sig_path}")
        signature_b64 = sig_path.read_text(encoding="utf-8").strip()
        if not verify_signature(pub_key, p.read_bytes(), signature_b64):
            raise RuntimeError("Risk budget signature verification failed")
    return rb

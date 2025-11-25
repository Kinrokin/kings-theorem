from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class RiskBudget:
    version: int
    catastrophic_max: float
    high_max: float
    medium_max: float
    min_samples: int
    last_approved_by: str | None = None


def load_risk_budget(config_path: str | Path = "config/risk_budget.yml") -> Optional[RiskBudget]:
    """Load risk budget with optional Ed25519 signature verification.

    Args:
        config_path: Path to risk_budget.yml

    Returns:
        RiskBudget if file exists, None otherwise

    Raises:
        RuntimeError: If signature verification enabled and fails
    """
    p = Path(config_path)
    if not p.exists():
        return None

    data = yaml.safe_load(p.read_text(encoding="utf-8"))

    # Optional signature verification (enabled via env to avoid breaking dev)
    if os.getenv("KT_VERIFY_RISK_BUDGET", "0") == "1":
        if "_signature" not in data:
            raise RuntimeError(f"Risk budget signature missing: {p}")

        # Verify Ed25519 signature
        try:
            from src.crypto import verify_json
        except ImportError:
            raise RuntimeError("Cryptographic signing not available (missing cryptography package)")

        if not verify_json(data):
            raise RuntimeError("Risk budget signature verification failed")

    rb = RiskBudget(
        version=int(data.get("version", 1)),
        catastrophic_max=float(data["catastrophic_max"]),
        high_max=float(data.get("high_max", 0.08)),
        medium_max=float(data.get("medium_max", 0.2)),
        min_samples=int(data.get("min_samples", 512)),
        last_approved_by=data.get("last_approved_by"),
    )

    return rb

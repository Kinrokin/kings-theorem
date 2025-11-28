"""Risk budget configuration loader."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

import yaml

PathLike = Union[str, Path]


@dataclass(frozen=True)
class RiskThresholds:
    """Container for risk budget limits and weighting."""

    catastrophic: Dict[str, float]
    severe: Dict[str, float]
    moderate: Dict[str, float]
    alpha: float
    weights: Dict[str, float]


def _resolve_config_path(path: Optional[PathLike]) -> Path:
    base_root = Path(__file__).resolve().parent.parent.parent
    if path is not None:
        return Path(path)
    return base_root / "config" / "risk_budget_v53.yaml"


def load_risk_budget(path: Optional[PathLike] = None) -> RiskThresholds:
    """Load the canonical risk budget configuration."""

    cfg_path = _resolve_config_path(path)
    with cfg_path.open("r", encoding="utf-8") as handle:
        raw: Mapping[str, Mapping[str, Mapping[str, float]]] = yaml.safe_load(handle)

    dims: Mapping[str, Mapping[str, float]] = raw["dimensions"]
    return RiskThresholds(
        catastrophic=dict(dims["catastrophic"]),
        severe=dict(dims["severe"]),
        moderate=dict(dims["moderate"]),
        alpha=float(raw.get("alpha", 0.999)),
        weights=dict(raw.get("weights", {})),
    )

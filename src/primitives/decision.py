from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RiskProfile:
    catastrophic_prob: float
    high_prob: float | None = None
    medium_prob: float | None = None
    samples: int = 0


@dataclass
class KTDecision:
    answer: Dict[str, Any]
    trace_id: str
    risk: Optional[RiskProfile] = None
    metadata: Dict[str, Any] = None

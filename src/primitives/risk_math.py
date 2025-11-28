"""
AID: /src/primitives/risk_math.py
Proof ID: PRF-RISK-001
Axiom: Axiom 1 (CVaR), Axiom 4 (Rho)
"""

from typing import Mapping

import numpy as np


def calculate_cvar(losses: np.ndarray, alpha: float = 0.95) -> float:
    if len(losses) == 0:
        return 0.0
    sorted_losses = np.sort(losses)
    index = int(alpha * len(sorted_losses))
    if index >= len(sorted_losses):
        return float(sorted_losses[-1])
    return np.mean(sorted_losses[index:])


def calculate_intracluster_correlation(data: np.ndarray) -> float:
    if len(data) < 2:
        return 0.0
    variance = np.var(data)
    if variance == 0:
        return 1.0
    return min(max(1.0 / (1.0 + variance), 0.0), 1.0)


def aggregate_risk(components: Mapping[str, float], weights: Mapping[str, float]) -> float:
    """Combine individual risk components via complement product.

    Uses 1 - Π (1 - w_i * r_i) formulation, constraining each weighted component
    to [0, 1] before multiplying. Result is also clamped to [0, 1].
    """

    prod = 1.0
    for key, raw_risk in components.items():
        weight = float(weights.get(key, 0.0))
        effective = max(0.0, min(1.0, weight * float(raw_risk)))
        prod *= 1.0 - effective
    return max(0.0, min(1.0, 1.0 - prod))

"""
AID: /src/primitives/risk_math.py
Proof ID: PRF-RISK-001
Axiom: Axiom 1 (CVaR), Axiom 4 (Rho)
Purpose: Core mathematical operations for risk and fatigue calculation.
"""
import numpy as np


def calculate_cvar(losses: np.ndarray, alpha: float = 0.95) -> float:
    """Calculates Conditional Value at Risk (CVaR)."""
    if len(losses) == 0:
        return 0.0
    sorted_losses = np.sort(losses)
    index = int(alpha * len(sorted_losses))
    if index >= len(sorted_losses):
        return float(sorted_losses[-1])
    return np.mean(sorted_losses[index:])


def calculate_intracluster_correlation(data: np.ndarray) -> float:
    """
    Calculates Rho (Fatigue/Groupthink metric).
    High correlation implies low cognitive diversity -> High Fatigue Risk.
    """
    if len(data) < 2:
        return 0.0
    variance = np.var(data)
    if variance == 0:
        return 1.0  # Total uniformity = Maximum correlation

    # Inverse relationship for the proxy
    rho = 1.0 / (1.0 + variance)
    return min(max(rho, 0.0), 1.0)

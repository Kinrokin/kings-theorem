"""
AID: /src/protocols/pfm_v1.py
Proof ID: PRF-PFM-001
Axiom: Axiom 4: Human-Factor Risk
"""
import numpy as np

from src.primitives.risk_math import calculate_intracluster_correlation


def check_fatigue_risk(operator_data: np.ndarray) -> str:
    rho = calculate_intracluster_correlation(operator_data)
    if rho > 0.6:
        return "REJECT_QUORUM (High Correlation)"
    return "ACCEPT_QUORUM"

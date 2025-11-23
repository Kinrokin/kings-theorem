from src.primitives.risk_math import calculate_intracluster_correlation
import numpy as np
def check_fatigue_risk(operator_data: np.ndarray) -> str:
    return "REJECT_QUORUM" if calculate_intracluster_correlation(operator_data) > 0.6 else "ACCEPT_QUORUM"

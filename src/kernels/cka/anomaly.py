import numpy as np
from numpy.linalg import norm
from src.metrics.spectral_guard import check_spectral_correlation # Used elsewhere
# Placeholder for build_weighted_deGroot_W and hessian_bounded_step 
# These are only used if a full CKA kernel is implemented but are not core to the demo
# They are retained for structural completeness (CKA is the folder name)

def spectral_norm_gated(W: np.ndarray, L_bound: float = 1.0) -> np.ndarray:
    svals = np.linalg.svd(W, compute_uv=False)
    sigma = float(np.max(svals)) if len(svals) else 0.0
    if sigma > L_bound:
        return W / (sigma / L_bound + 1e-12)
    return W

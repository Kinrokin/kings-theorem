import numpy as np


def check_spectral_correlation(weights_a: np.ndarray, weights_b: np.ndarray, threshold: float = 0.92) -> bool:
    vec_a = weights_a.flatten()
    vec_b = weights_b.flatten()
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return False
    correlation = np.dot(vec_a, vec_b) / (norm_a * norm_b)
    return abs(correlation) > threshold

import numpy as np


def detect_adaptive_replay_anomaly(series: np.ndarray, short_win=50, long_win=200, threshold=3.0) -> bool:
    """
    Adaptive Replay Guard. Compares short-term residual variance against long-term baseline.
    Catches botnets that try to normalize their traffic pattern.
    """
    if len(series) < long_win:
        return False
    long_hist = series[-long_win:]
    short_hist = series[-short_win:]
    long_std = np.std(long_hist)
    short_std = np.std(short_hist)
    # If variance collapses -> Artificial Stasis
    return short_std < (long_std / threshold)


def detect_adversarial_flood(
    x: np.ndarray, window: int = 50, entropy_min: float = 1.5, spike_sigma: float = 4.0
) -> bool:
    """
    Flood Guard. Detects low-entropy, high-variance spikes.
    """
    n = x.shape[0]
    if n < window:
        return False
    w = x[-window:]
    dist = np.abs(w) / (np.sum(np.abs(w)) + 1e-12)

    # Shannon Entropy
    q = np.clip(dist, 1e-12, 1.0)
    ent = float(-np.sum(q * np.log(q)))

    std = float(np.std(w))
    baseline_std = float(np.std(x[:-window])) if n > window else std
    spike = (std - baseline_std) > spike_sigma * (baseline_std + 1e-12)

    return spike and (ent < entropy_min)

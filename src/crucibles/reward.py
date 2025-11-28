#!/usr/bin/env python3
"""
Composite Reward Function - The Intelligence Barometer
Provides scalar objective signal for curriculum quality assessment.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RewardComponents:
    """
    Scalar metrics used to compute the composite reward.

    All values are expected in [0, 1] where possible.
    - contamination_rate: fraction of contaminated/invalid samples (0 = perfect).
    - compression_density: how dense/concise compressed answers are (higher is better).
    - fractal_score_gain: improvement from initial to final scores (0-1).
    - drift_variance: variance of ontological/token drift (0 = perfectly stable).
    """
    contamination_rate: float
    compression_density: float
    fractal_score_gain: float
    drift_variance: float


@dataclass
class RewardWeights:
    """
    Tunable weights for the composite reward.

    You can tweak these based on what you care about most.
    Default distribution prioritizes contamination prevention.
    """
    w_contamination: float = 0.40
    w_compression: float = 0.20
    w_fractal_gain: float = 0.25
    w_drift: float = 0.15


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, value))


def compute_reward(
    components: RewardComponents,
    weights: Optional[RewardWeights] = None,
) -> float:
    """
    Composite reward function for Ouroboros.

    Reward =
        w1 * (1 - contamination_rate)
      + w2 * compression_density
      + w3 * fractal_score_gain
      + w4 * (1 - drift_variance)

    Args:
        components: Measured metrics from harvest
        weights: Optional custom weights (uses defaults if None)

    Returns:
        Scalar reward in [0, 1] range
    """
    if weights is None:
        weights = RewardWeights()

    c = components

    # Convert components to reward signals (higher is better)
    cont = _clamp(1.0 - c.contamination_rate)
    comp = _clamp(c.compression_density)
    fractal = _clamp(c.fractal_score_gain)
    drift = _clamp(1.0 - c.drift_variance)

    reward = (
        weights.w_contamination * cont
        + weights.w_compression * comp
        + weights.w_fractal_gain * fractal
        + weights.w_drift * drift
    )

    # Final clamp to ensure [0, 1]
    return _clamp(reward)


def analyze_reward_breakdown(
    components: RewardComponents,
    weights: Optional[RewardWeights] = None,
) -> dict:
    """
    Detailed breakdown of reward components for debugging.

    Returns:
        Dictionary with per-component contributions and total reward
    """
    if weights is None:
        weights = RewardWeights()

    c = components

    cont = _clamp(1.0 - c.contamination_rate)
    comp = _clamp(c.compression_density)
    fractal = _clamp(c.fractal_score_gain)
    drift = _clamp(1.0 - c.drift_variance)

    return {
        "contamination_contribution": weights.w_contamination * cont,
        "compression_contribution": weights.w_compression * comp,
        "fractal_contribution": weights.w_fractal_gain * fractal,
        "drift_contribution": weights.w_drift * drift,
        "total_reward": compute_reward(components, weights),
        "raw_components": {
            "contamination_rate": c.contamination_rate,
            "compression_density": c.compression_density,
            "fractal_score_gain": c.fractal_score_gain,
            "drift_variance": c.drift_variance,
        },
    }

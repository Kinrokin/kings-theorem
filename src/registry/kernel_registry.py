from __future__ import annotations

from random import SystemRandom

_RNG = SystemRandom()


class BaseKernel:
    def __init__(self, name: str):
        self.name = name

    def process(self, input_data):  # pragma: no cover simple stub
        raise NotImplementedError


class SafetyKernel(BaseKernel):
    def process(self, input_data):
        # Emits moderate numeric values signalling safety influence
        return {"safety_score": _RNG.uniform(0.4, 0.9), "stable": True}


class RiskActionKernel(BaseKernel):
    def process(self, input_data):
        # Emits risky numeric values with calibrated tail probabilities
        roll = _RNG.random()
        if roll < 0.03:  # 3% NaN (critical numerical failure)
            base = float("nan")
        elif roll < 0.10:  # next 7% extreme values just over 1e6
            base = _RNG.uniform(1.1e6, 2.0e6)
        else:  # 90% moderate risk stays below extreme threshold
            base = _RNG.uniform(2e5, 8e5)
        return {
            "risk_metric": base,
            "stable": (isinstance(base, float) and not (base != base)) and base < 1e6,
        }


class CompositionKernel(BaseKernel):
    def process(self, input_data):
        # Emits boolean facts with intentional contradictions (30% of time)
        flip = _RNG.choice([True, False])
        if _RNG.random() < 0.25:  # 25% contradiction to reduce cascade while preserving pressure
            return {"fact_A": True, "fact_B": True, "contradictory": True}
        return {"fact_A": flip, "fact_B": not flip, "contradictory": False}


class AmplifierKernel(BaseKernel):
    """Compounds existing violations by emitting additional extreme/NaN values."""

    def process(self, input_data):
        roll = _RNG.random()
        if roll < 0.05:  # 5% NaN amplification
            return {
                "amplified_metric": float("nan"),
                "amplification_factor": float("inf"),
            }
        elif roll < 0.15:  # next 10% extreme amplification (reduced magnitude)
            return {
                "amplified_metric": _RNG.uniform(1.5e6, 5e6),
                "amplification_factor": 25,
            }
        return {"amplified_metric": _RNG.uniform(5e3, 5e4), "amplification_factor": 1}


def load_kernel_registry():
    """Return a representative registry of kernels for counterfactual sampling."""
    return {
        "safety_kernel": SafetyKernel("safety_kernel"),
        "risk_action_kernel": RiskActionKernel("risk_action_kernel"),
        "composition_kernel": CompositionKernel("composition_kernel"),
        "amplifier_kernel": AmplifierKernel("amplifier_kernel"),
    }

from __future__ import annotations

import random


class BaseKernel:
    def __init__(self, name: str):
        self.name = name

    def process(self, input_data):  # pragma: no cover simple stub
        raise NotImplementedError


class SafetyKernel(BaseKernel):
    def process(self, input_data):
        # Emits moderate numeric values signalling safety influence
        return {"safety_score": random.uniform(0.4, 0.9), "stable": True}


class RiskActionKernel(BaseKernel):
    def process(self, input_data):
        # Emits catastrophic numeric values triggering HIGH/CRITICAL violations
        roll = random.random()
        if roll < 0.15:  # 15% NaN (CRITICAL: +0.4 score)
            base = float("nan")
        elif roll < 0.35:  # 20% extreme values (HIGH: +0.2 score)
            base = random.uniform(2e6, 5e6)
        else:  # 65% moderate risk
            base = random.uniform(5e5, 1.5e6)
        return {
            "risk_metric": base,
            "stable": (isinstance(base, float) and not (base != base)) and base < 1e6,
        }


class CompositionKernel(BaseKernel):
    def process(self, input_data):
        # Emits boolean facts with intentional contradictions (30% of time)
        flip = random.choice([True, False])
        if random.random() < 0.3:  # 30% contradiction (MEDIUM/HIGH: +0.3 score)
            return {"fact_A": True, "fact_B": True, "contradictory": True}
        return {"fact_A": flip, "fact_B": not flip, "contradictory": False}


class AmplifierKernel(BaseKernel):
    """Compounds existing violations by emitting additional extreme/NaN values."""

    def process(self, input_data):
        roll = random.random()
        if roll < 0.2:  # 20% NaN amplification
            return {
                "amplified_metric": float("nan"),
                "amplification_factor": float("inf"),
            }
        elif roll < 0.4:  # 20% extreme amplification
            return {
                "amplified_metric": random.uniform(8e6, 1e8),
                "amplification_factor": 100,
            }
        return {"amplified_metric": random.uniform(1e3, 1e5), "amplification_factor": 1}


def load_kernel_registry():
    """Return a representative registry of kernels for counterfactual sampling."""
    return {
        "safety_kernel": SafetyKernel("safety_kernel"),
        "risk_action_kernel": RiskActionKernel("risk_action_kernel"),
        "composition_kernel": CompositionKernel("composition_kernel"),
        "amplifier_kernel": AmplifierKernel("amplifier_kernel"),
    }

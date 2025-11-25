from __future__ import annotations

from typing import Any, Dict, Optional

from src.primitives.decision import KTDecision, RiskProfile
from src.reasoning.counterfactual_engine import CounterfactualEngine
from src.registry.kernel_registry import load_kernel_registry
from src.risk.budget import RiskBudget, load_risk_budget


def run_counterfactuals(samples: int = 512, rng_seed: int = 99) -> RiskProfile:
    engine = CounterfactualEngine(kernel_registry=load_kernel_registry(), rng_seed=rng_seed)
    catastrophic = engine.sample_violation_probability(samples=samples)
    # For now, only catastrophic probability is computed; placeholders for future buckets
    return RiskProfile(
        catastrophic_prob=catastrophic,
        high_prob=None,
        medium_prob=None,
        samples=samples,
    )


def exceeds_budget(risk: RiskProfile, budget: RiskBudget) -> bool:
    if risk.samples < budget.min_samples:
        # If undersampled, treat as exceeding until we have enough evidence
        return True
    return risk.catastrophic_prob > budget.catastrophic_max


def enforce_safe_fallback(decision: KTDecision) -> KTDecision:
    # Replace with conservative response and attach reason
    fallback = {
        "outcome": "REFUSED",
        "reason": "Risk budget exceeded; safe fallback engaged",
        "trace_id": decision.trace_id,
    }
    return KTDecision(
        answer=fallback,
        trace_id=decision.trace_id,
        risk=decision.risk,
        metadata=decision.metadata,
    )


def finalize_decision(raw_answer: Dict[str, Any], trace_id: str, budget: Optional[RiskBudget] = None) -> KTDecision:
    decision = KTDecision(answer=raw_answer, trace_id=trace_id, metadata={})
    # Load budget if not provided
    budget = budget or load_risk_budget()
    if not budget:
        # No budget configured; return as-is
        return decision
    risk = run_counterfactuals(samples=budget.min_samples)
    decision.risk = risk
    if exceeds_budget(risk, budget):
        return enforce_safe_fallback(decision)
    return decision

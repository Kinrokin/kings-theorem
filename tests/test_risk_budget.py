from src.governance.risk_budget import load_risk_budget
from src.primitives.risk_math import aggregate_risk


def test_load_risk_budget_defaults():
    thresholds = load_risk_budget()
    assert thresholds.catastrophic["max_prob"] == 0.03
    assert thresholds.severe["max_cvar"] == 0.6
    assert "guardrail_violation" in thresholds.weights


def test_aggregate_risk_weighting():
    weights = {
        "guardrail_violation": 1.0,
        "constraint_tension": 0.8,
        "low_warrant": 0.4,
    }
    components = {
        "guardrail_violation": 1.0,
        "constraint_tension": 0.5,
        "low_warrant": 0.5,
    }
    combined = aggregate_risk(components, weights)
    assert 0.6 < combined <= 1.0

    low_risk = aggregate_risk({"guardrail_violation": 0.0}, weights)
    assert low_risk == 0.0

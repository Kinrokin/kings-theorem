from src.governance.tri_governor import TriGovernor


def test_catastrophic_risk_forces_tier5():
    tg = TriGovernor()
    decision = tg.adjudicate(
        {
            "tags": [],
            "integrity_violation": False,
            "replay_confidence": 0.9,
            "warrant": 0.9,
            "aggregate_risk": 0.95,
            "constraint_tension": 0.2,
        }
    )
    assert decision["decision"] == "TIER_5_HALT"


def test_moderate_risk_low_warrant_drops():
    tg = TriGovernor()
    decision = tg.adjudicate(
        {
            "tags": [],
            "integrity_violation": False,
            "replay_confidence": 0.9,
            "warrant": 0.3,
            "aggregate_risk": 0.25,
            "constraint_tension": 0.1,
        }
    )
    assert decision["decision"] == "DROP"


def test_low_risk_executes():
    tg = TriGovernor()
    decision = tg.adjudicate(
        {
            "tags": [],
            "integrity_violation": False,
            "replay_confidence": 0.95,
            "warrant": 0.95,
            "aggregate_risk": 0.05,
            "constraint_tension": 0.05,
        }
    )
    assert decision["decision"] == "EXECUTE"

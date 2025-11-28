import pytest

from src.core.kt_engine import KTEngine
from tests.phase4_utils import build_problem_graph, configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def test_guardrail_violation_forces_non_execute():
    engine = KTEngine()
    graph = build_problem_graph(
        "Attempt to sacrifice civilians",
        tags=["replay_alert"],
        action_type="SACRIFICE_MINORITY",
        constraint="RISK < 5% AND ZERO HARM",
    )
    result = engine.execute(graph)

    decision = result.get("governance", {}).get("decision")
    assert decision in {"HALT", "TIER_5_HALT", "FREEZE", "DROP"}, "Governance should not EXECUTE unsafe plans"
    assert result.get("risk", {}).get("aggregate", 0.0) >= 0.4


def test_low_risk_plan_executes():
    engine = KTEngine()
    graph = build_problem_graph(
        "Expand civic services portal",
        tags=[],
        action_type="BENIGN_ACTION",
    )
    result = engine.execute(graph)

    decision = result.get("governance", {}).get("decision")
    assert decision == "EXECUTE"
    assert result.get("risk", {}).get("tier") == "LOW"
    assert result.get("trace_valid") is True

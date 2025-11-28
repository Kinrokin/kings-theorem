import pytest

from src.core.kt_engine import KTEngine
from tests.phase4_utils import build_problem_graph, configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def test_contradiction_short_circuits_engine():
    engine = KTEngine()
    graph = build_problem_graph(
        "Maximize profit with impossible zero-risk demand",
        constraint="MAXIMIZE PROFIT while ZERO RISK simultaneously",
        tags=["interactive"],
    )
    result = engine.execute(graph)

    assert result["status"] == "CONSTRAINT_CONTRADICTION"
    assert result.get("risk", {}).get("aggregate") == 0.0
    assert result.get("trace") == []


def test_risk_bounds_reflected_in_response():
    engine = KTEngine()
    graph = build_problem_graph(
        "Exploit market with prohibited action",
        constraint="RISK < 5% AND ZERO HARM",
        tags=["replay_alert"],
        action_type="SACRIFICE_MINORITY",
    )
    result = engine.execute(graph)

    constraints = result.get("constraints", {}).get("constraints", {})
    assert constraints.get("risk_bounds") == [5]
    assert result.get("risk", {}).get("aggregate", 0.0) >= 0.4
    assert result.get("status") in {"VETOED", "TIER_5_HALT", "HALT"}

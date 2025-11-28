import pytest
from fastapi.testclient import TestClient

from src.server import app
from tests.phase4_utils import build_problem_graph, configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def _build_request(problem_id: str = "API_TRACE_001"):
    graph = build_problem_graph(
        "Trace invariant validation",
        constraint="RISK < 20% AND MAXIMIZE SAFETY",
        tags=["replay_alert"],
        action_type="BENIGN_ACTION",
    )
    return {"problem_id": problem_id, "problem_graph": graph}


def test_trace_contains_governance_phase():
    client = TestClient(app)
    response = client.post("/solve", json=_build_request("API_TRACE_PHASE4"))
    assert response.status_code == 200

    payload = response.json()
    trace = payload.get("trace")
    assert isinstance(trace, list) and trace, "Trace should be a non-empty list"

    phases = [event.get("phase") for event in trace]
    assert "TRIGOVERNOR" in phases, "TriGovernor decisions must be represented in the trace"
    assert "BROKER" in phases, "DecisionBroker events must be recorded"

    for event in trace:
        assert {"phase", "name", "status"}.issubset(event.keys())
        assert isinstance(event.get("meta"), dict)

    assert payload.get("governance"), "Governance block must be present in API response"

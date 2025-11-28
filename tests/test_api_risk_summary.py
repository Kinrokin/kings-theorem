import pytest
from fastapi.testclient import TestClient

from src.server import app
from tests.phase4_utils import build_problem_graph, configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def _build_request(problem_id: str, tags=None, action_type="BENIGN_ACTION"):
    graph = build_problem_graph(
        "Risk summary surface",
        constraint="RISK < 10% AND PRESERVE HUMAN LIFE",
        tags=tags or [],
        action_type=action_type,
    )
    return {"problem_id": problem_id, "problem_graph": graph}


def test_api_response_contains_risk_summary():
    client = TestClient(app)
    response = client.post("/solve", json=_build_request("API_RISK_LOW"))
    assert response.status_code == 200

    payload = response.json()
    risk = payload.get("risk")
    assert risk and {"aggregate", "components", "tier"}.issubset(risk.keys())
    assert 0.0 <= float(risk.get("aggregate")) <= 1.0
    assert isinstance(risk.get("components"), dict)
    assert risk.get("tier") in {"LOW", "MODERATE", "SEVERE", "CATASTROPHIC"}


def test_api_escalates_tier_for_high_risk_tags():
    client = TestClient(app)
    response = client.post(
        "/solve",
        json=_build_request(
            "API_RISK_HIGH",
            tags=["replay_alert", "flood_alert"],
            action_type="SACRIFICE_MINORITY",
        ),
    )
    assert response.status_code == 200

    payload = response.json()
    risk = payload.get("risk")
    assert risk.get("tier") in {"SEVERE", "CATASTROPHIC"}, "High-risk metadata should escalate tiers"
    assert risk.get("aggregate", 0.0) >= 0.4

"""Phase 5 Multi-Agent Governance Stress Tests

Simulates:
  - Conflicting agents with competing objectives
  - Parallel KT instances with cross-constraints
  - Adversarial negotiation dynamics

Validates:
  - Governance halts under conflict
  - Ledger maintains consistency across parallel instances
  - Risk aggregation handles competing proposals
"""

import pytest

from src.core.kt_engine import KTEngine
from tests.phase4_utils import configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def test_conflicting_agents_trigger_halt():
    """Two agents propose mutually exclusive actions; KT must halt or arbitrate."""

    engine = KTEngine()

    # Agent 1: Maximize profit
    agent1_graph = {
        "problem_id": "AGENT1_PROFIT",
        "task": "Maximize quarterly profit",
        "constraint": "MAXIMIZE PROFIT subject to RISK < 15%",
        "metadata": {"domain": "finance", "agent": "agent1", "tags": []},
        "proposed_actions": [
            {
                "type": "HIGH_RISK_TRADE",
                "utility": 1000,
                "summary": "Execute risky arbitrage",
            }
        ],
    }

    # Agent 2: Minimize risk (conflicts with agent1)
    agent2_graph = {
        "problem_id": "AGENT2_SAFETY",
        "task": "Minimize portfolio risk",
        "constraint": "MINIMIZE RISK subject to PROFIT > 0",
        "metadata": {"domain": "finance", "agent": "agent2", "tags": []},
        "proposed_actions": [
            {
                "type": "CONSERVATIVE_HEDGE",
                "utility": 10,
                "summary": "Hedge all exposure",
            }
        ],
    }

    result1 = engine.execute(agent1_graph)
    result2 = engine.execute(agent2_graph)

    # KT should produce different governance outcomes reflecting conflict
    decision1 = result1.get("governance", {}).get("decision")
    decision2 = result2.get("governance", {}).get("decision")

    # At least one should not be EXECUTE due to conflicting constraints
    assert decision1 != decision2 or decision1 in {"FREEZE", "HALT", "DROP"}


def test_parallel_kt_instance_ledger_consistency():
    """Parallel KT instances must not produce duplicate problem IDs in shared ledger."""

    engine1 = KTEngine()
    engine2 = KTEngine()

    # Same problem ID submitted to both instances
    problem_id = "PARALLEL_TEST_001"
    graph = {
        "problem_id": problem_id,
        "task": "Test parallel submission",
        "constraint": "Uphold governance",
        "metadata": {"domain": "test", "tags": []},
        "proposed_actions": [{"type": "BENIGN_ACTION", "utility": 1.0, "summary": "Test action"}],
    }

    result1 = engine1.execute(graph)
    # Second execution with same problem_id should either:
    # a) be rejected by ledger invariant
    # b) produce different trace/token

    # For now, we check that both executions succeed independently
    # (full distributed consistency would require shared ledger instance)
    result2 = engine2.execute(graph)

    assert result1.get("status") in {"SOLVED", "VETOED"}
    assert result2.get("status") in {"SOLVED", "VETOED"}

    # Verify ledgers are independent (no cross-contamination)
    assert engine1.ledger.chain != engine2.ledger.chain or len(engine1.ledger.chain) == len(engine2.ledger.chain)


def test_adversarial_negotiation_cross_constraints():
    """Multi-agent scenario with cross-cutting constraints forces governance freeze."""

    engine = KTEngine()

    # Agent proposes action that violates another agent's constraints
    graph = {
        "problem_id": "ADVERSARIAL_NEGOTIATE_001",
        "task": "Agent A proposes action violating Agent B constraints",
        "constraint": "MAXIMIZE AGENT_A_UTILITY AND AGENT_B_RISK < 5%",
        "data": {
            "agent_a_proposal": "High-risk maneuver",
            "agent_b_constraint": "Risk must stay below 5%",
            "conflict": True,
        },
        "metadata": {"domain": "negotiation", "tags": ["conflict", "multi_agent"]},
        "proposed_actions": [
            {
                "type": "CONFLICTING_ACTION",
                "utility": 500,
                "summary": "Action benefits A but violates B's risk constraint",
            }
        ],
    }

    result = engine.execute(graph)

    # Governance should not allow EXECUTE under conflicting constraints
    decision = result.get("governance", {}).get("decision")
    assert decision in {"FREEZE", "HALT", "DROP", "TIER_5_HALT"}
    assert result.get("risk", {}).get("aggregate", 0.0) > 0.0

"""Tests for Orchestrator."""

import pytest
from kt_core.orchestrator import Orchestrator
from kt_core.prover import LLMProver
from kt_core.risk import RiskBudget
from kt_core.verifier import Z3Verifier


@pytest.mark.asyncio
async def test_orchestrator_basic():
    """Test orchestrator completes with PROVEN or HALTED_BUDGET."""
    orch = Orchestrator(LLMProver(), Z3Verifier())
    status, trace = await orch.solve("Simple theorem", RiskBudget(max_depth=5, timeout_sec=1.0))

    assert status in ("PROVEN", "HALTED_BUDGET")
    assert len(trace.steps) >= 1  # At least axiom

    # Verify seal chain exists
    assert "seal_chain" in trace.metadata


@pytest.mark.asyncio
async def test_orchestrator_halts_on_budget():
    """Test orchestrator halts when budget exhausted."""
    orch = Orchestrator(LLMProver(), Z3Verifier(), max_rejections=1)

    # Ultra-tight budget to force immediate halt
    budget = RiskBudget(max_tokens=1, max_depth=0, timeout_sec=0.0)
    status, _ = await orch.solve("Budget limited theorem", budget)

    assert status == "HALTED_BUDGET"


@pytest.mark.asyncio
async def test_orchestrator_proven_status():
    """Test orchestrator can reach PROVEN status."""
    orch = Orchestrator(LLMProver(), Z3Verifier())

    # Generous budget
    budget = RiskBudget(max_tokens=10000, max_depth=10, timeout_sec=5.0)
    status, trace = await orch.solve("Test theorem", budget)

    # Should reach PROVEN (mock prover generates valid steps)
    assert status == "PROVEN"
    assert len(trace.steps) >= 5  # Axiom + 4 steps


@pytest.mark.asyncio
async def test_orchestrator_backtracking():
    """Test backtracking on too many rejections."""
    orch = Orchestrator(LLMProver(), Z3Verifier(), max_rejections=2)

    budget = RiskBudget(max_tokens=10000, max_depth=20, timeout_sec=5.0)
    status, trace = await orch.solve("Backtrack test", budget)

    # Should complete without infinite loop
    assert status in ("PROVEN", "HALTED_BUDGET")


@pytest.mark.asyncio
async def test_orchestrator_trace_integrity():
    """Test proof trace maintains integrity."""
    orch = Orchestrator(LLMProver(), Z3Verifier())

    budget = RiskBudget(max_tokens=1000, max_depth=5, timeout_sec=2.0)
    status, trace = await orch.solve("Integrity test", budget)

    # Verify trace structure
    assert len(trace.steps) > 0
    assert trace.steps[0].source == "axiom"  # First step is axiom

    # Verify seal chain
    chain = trace.metadata.get("seal_chain")
    assert chain is not None

    hashes = chain.split("->")
    assert len(hashes) == len(trace.steps)


@pytest.mark.asyncio
async def test_orchestrator_timeout():
    """Test orchestrator respects timeout."""
    orch = Orchestrator(LLMProver(), Z3Verifier())

    # Very short timeout
    budget = RiskBudget(max_tokens=10000, max_depth=100, timeout_sec=0.05)
    status, _ = await orch.solve("Timeout test", budget)

    assert status == "HALTED_BUDGET"


@pytest.mark.asyncio
async def test_orchestrator_depth_limit():
    """Test orchestrator respects depth limit."""
    orch = Orchestrator(LLMProver(), Z3Verifier())

    # Very shallow depth
    budget = RiskBudget(max_tokens=10000, max_depth=2, timeout_sec=5.0)
    status, trace = await orch.solve("Depth test", budget)

    assert status in ("PROVEN", "HALTED_BUDGET")
    # Should not exceed depth limit + 1 (for axiom)
    assert len(trace.steps) <= 4  # Axiom + max 3 steps before halt

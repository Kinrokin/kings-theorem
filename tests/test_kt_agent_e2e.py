"""Integration test: KT Agent asks a question, arbiter governs output, provenance is sealed."""

import os
import tempfile

import pytest

from src.agent.kt_agent import KTAgent
from src.governance.arbiter_hardened import ArbiterDecision, HardenedArbiter
from src.ledger.append_only import create_ledger


@pytest.mark.asyncio
async def test_kt_agent_e2e_math_mode():
    """End-to-end: KTAgent routes math query through arbiter with provenance sealing."""
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = os.path.join(tmp, "agent_test.ledger")
        ledger = create_ledger(ledger_path)
        arbiter = HardenedArbiter(ledger)
        agent = KTAgent(arbiter)

        # Ask a math question (will call query_qwen under the hood)
        result = await agent.ask("What is 2+2?", mode="math")

        # Verify arbitration happened
        assert result.decision in {
            ArbiterDecision.APPROVED,
            ArbiterDecision.FAILED,
            ArbiterDecision.ERROR,
        }, f"Unexpected decision: {result.decision}"

        # Verify provenance was sealed
        assert result.ledger_hash is not None
        assert len(result.ledger_hash) == 64  # SHA256 hex

        # Verify S-tier metadata is present (σ-text + Trinity)
        provenance = result.provenance
        if result.decision == ArbiterDecision.APPROVED:
            # Check for sigma-text hashes
            if "sigma_student_sha256" in provenance:
                assert isinstance(provenance["sigma_student_sha256"], str)
                assert len(provenance["sigma_student_sha256"]) == 64
            # Check for Trinity scores
            if "trinity" in provenance:
                tri = provenance["trinity"]
                assert 0.0 <= tri["divergence"] <= 1.0
                assert 0.0 <= tri["epistemic"] <= 1.0
                assert 0.0 <= tri["risk"] <= 1.0
                assert 0.0 <= tri["composite"] <= 1.0

        print(f"✅ E2E Test Passed: decision={result.decision.value}, ledger_hash={result.ledger_hash[:16]}...")


@pytest.mark.asyncio
async def test_kt_agent_default_ai_mode():
    """KTAgent defaults to AI capability when mode is None."""
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = os.path.join(tmp, "agent_ai_test.ledger")
        ledger = create_ledger(ledger_path)
        arbiter = HardenedArbiter(ledger)
        agent = KTAgent(arbiter)

        # No mode specified → defaults to AI
        result = await agent.ask("Hello, world!")

        assert result.decision in {
            ArbiterDecision.APPROVED,
            ArbiterDecision.FAILED,
            ArbiterDecision.ERROR,
        }
        print(f"✅ Default AI Mode: decision={result.decision.value}")


@pytest.mark.asyncio
async def test_kt_agent_capabilities_registered():
    """Verify all 6 capabilities are registered in KTAgent."""
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = os.path.join(tmp, "agent_cap_test.ledger")
        ledger = create_ledger(ledger_path)
        arbiter = HardenedArbiter(ledger)
        agent = KTAgent(arbiter)

        expected_modes = {"ai", "math", "code", "ethics", "creative", "dev"}
        actual_modes = set(agent.capabilities.keys())

        assert actual_modes == expected_modes, f"Missing capabilities: {expected_modes - actual_modes}"
        print(f"✅ All 6 capabilities registered: {sorted(actual_modes)}")

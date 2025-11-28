"""
AID: /src/main.py
Proof ID: PRF-ARB-008A
Purpose: Master Controller Entrypoint.
"""

import asyncio
import logging
import os
import sys

# KT Path Correction Axiom (ensure parent directory on path before package imports)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logging_config import setup_logging  # noqa: E402

setup_logging()
from src.core.kt_engine import KTEngine  # noqa: E402
from src.governance.nemo_guard import TitaniumGuardrail  # noqa: E402
from src.governance.semantic_guard import get_semantic_guard  # noqa: E402
from src.kernels.raft_arbiter import RaftArbiter  # noqa: E402
from src.primitives.axiomatic_verifier import AxiomaticVerifier  # noqa: E402
from src.primitives.merkle_ledger import MerkleLedger  # noqa: E402

logger = logging.getLogger(__name__)


def run_system():
    logger.info("[BOOT] Initializing Canonical KTEngine (Phoenix Phase 1)...")
    engine = KTEngine()
    test_problem = {
        "task": "Whistleblower",
        "proposed_actions": [{"type": "SACRIFICE_MINORITY", "utility": 999}],
        "module3_planning": {"constraints": {"E_peak_threshold": 45}},
        "data": {},
        "constraint": "Minimize ethical violations while maximizing truth clarity.",
    }
    result = engine.execute(test_problem)
    logger.info(
        "\n[FINAL SYSTEM RULING] Status: %s | Decision: %s",
        result.get("status"),
        result.get("governance", {}).get("decision"),
    )
    risk = result.get("risk", {})
    logger.info(
        "[RISK] Tier=%s Aggregate=%.3f Components=%s",
        risk.get("tier", "LOW"),
        float(risk.get("aggregate", 0.0) or 0.0),
        risk.get("components", {}),
    )
    logger.info("[TRACE] %d events captured", len(result.get("trace", [])))


async def run_titanium_cycle(problem: dict):
    """Execute Titanium X cycle: SemanticGuard → Guardrail → Z3 Verify → Raft → Merkle.

    Adds Hybrid Neuro-Symbolic pre-veto (SemanticGuard) before legacy TitaniumGuardrail
    to catch obfuscated / synonym-based harmful intent.
    """
    # Phase 0: Neuro-Symbolic intent assessment (pre-computation veto)
    semantic_guard = get_semantic_guard()
    sg_result = semantic_guard.assess(problem.get("task", ""))
    if sg_result.is_blocked:
        logger.warning(
            "SemanticGuard BLOCK: reason=%s semantic=%.3f fuzzy=%.1f latency_ms=%d",
            sg_result.reason,
            sg_result.semantic_score,
            sg_result.fuzzy_score,
            sg_result.latency_ms,
        )
        return "BLOCKED_BY_SEMANTIC_GUARD"

    # Phase 1: Existing ethical guardrails (Axiom 6 enforcement)
    guard = TitaniumGuardrail()
    passed = await guard.vet(problem.get("task", ""))
    if not passed:
        logger.warning("Cycle blocked by Axiom 6 (guardrail veto)")
        return "BLOCKED_BY_AXIOM_6"

    verifier = AxiomaticVerifier()
    safe, model = verifier.verify_with_proof(problem.get("state", {"profit": 1.0, "risk": 0.4}))
    if not safe:
        print("[VERIFIER] UNSAFE STATE DETECTED.")
        print("[VERIFIER] Model:")
        print(model)
        return "BLOCKED_BY_AXIOM_2"

    arbiter = RaftArbiter("localhost:4321", [])  # single-node demo
    # Single authoritative decision entry replicated via Raft
    decision = {"id": "sol_1", "status": "PASS"}
    accepted = arbiter.propose(decision)
    if not accepted:
        logger.info("[CONSENSUS] Decision forwarded; running in follower mode")

    ledger = MerkleLedger()
    root = ledger.add_entry(decision)
    seal = ledger.seal_ledger()
    logger.info(
        "TitaniumCycle Safe=%s MerkleRoot=%s Seal=%s DecisionStatus=%s RaftAccepted=%s",
        safe,
        root[:16],
        seal[:16],
        decision.get("status"),
        accepted,
    )
    return "TITANIUM_CYCLE_COMPLETE"


def run_demo_cycle():
    problem = {"task": "Assess portfolio", "state": {"profit": 2.0, "risk": 0.3}}
    asyncio.run(run_titanium_cycle(problem))


if __name__ == "__main__":
    run_system()
    run_demo_cycle()

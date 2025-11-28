"""Titanium X Main Orchestration

AID: /main.py
Purpose: Production-hardened Titanium cycle demonstration

Orchestration Flow:
1. Guardrail vetting (Axiom 6)
2. Z3 formal verification (Axiom 2)
3. Raft consensus commitment (Axiom 5)
4. Merkle ledger sealing (Axiom 3)
"""

import asyncio

from src.governance.nemo_guard import TitaniumGuardrail
from src.kernels.raft_arbiter import RaftArbiter
from src.primitives.axiomatic_verifier import AxiomaticVerifier
from src.primitives.merkle_ledger import MerkleLedger


async def run_titanium_cycle(problem):
    """Execute complete Titanium X verification cycle.

    Args:
        problem: Dictionary with 'desc' and 'state' keys

    Returns:
        Status string indicating cycle result
    """
    # PHASE 1: Ethical Guardrail (Axiom 6)
    guard = TitaniumGuardrail()
    if not await guard.vet(problem["desc"]):
        print("[TITANIUM] BLOCKED_BY_AXIOM_6")
        return "BLOCKED_BY_AXIOM_6"

    # PHASE 2: Formal Safety Verification (Axiom 2)
    verifier = AxiomaticVerifier()
    is_safe, proof = verifier.verify_with_proof(problem["state"])
    print(proof)

    if not is_safe:
        print("[TITANIUM] BLOCKED_BY_AXIOM_2")
        return "BLOCKED_BY_AXIOM_2"

    # PHASE 3: Distributed Consensus (Axiom 5)
    arbiter = RaftArbiter("localhost:4321", [])
    decision = {"id": "sol1", "status": "PASS"}
    arbiter.propose(decision)

    # PHASE 4: Cryptographic Ledger (Axiom 3)
    ledger = MerkleLedger()
    ledger.log(decision)
    seal = ledger.seal_ledger()
    print(f"[LEDGER] Seal: {seal[:16]}...")

    print("[TITANIUM] TITANIUM_CYCLE_COMPLETE")
    return "TITANIUM_CYCLE_COMPLETE"


if __name__ == "__main__":
    # Safe scenario (should pass all checks)
    safe_problem = {"desc": "Assess portfolio risk with ethical bounds", "state": {"profit": 1.0, "risk": 0.1}}

    result = asyncio.run(run_titanium_cycle(safe_problem))
    print(f"\n[FINAL] {result}")

    # Unsafe scenario (should fail Axiom 2)
    print("\n" + "=" * 60)
    unsafe_problem = {"desc": "High-risk investment strategy", "state": {"profit": 10.0, "risk": 0.9}}

    result2 = asyncio.run(run_titanium_cycle(unsafe_problem))
    print(f"\n[FINAL] {result2}")

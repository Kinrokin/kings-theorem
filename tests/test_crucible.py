"""Crucible Test Suite - Titanium X Protocol

AID: /tests/test_crucible.py
Purpose: Adversarial testing for formal verification and tamper detection

Test Categories:
1. Paradox Bomb: High-risk states that should trigger UNSAT
2. History Rewrite: Tampering detection via Merkle integrity
"""

from src.primitives.axiomatic_verifier import AxiomaticVerifier
from src.primitives.merkle_ledger import MerkleLedger


def test_paradox_bomb():
    """Test that high-risk states are correctly rejected by Z3 solver."""
    verifier = AxiomaticVerifier(risk_threshold=0.5)

    # This state violates safety: profit > 0 AND risk >= 0.5
    unsafe_state = {"profit": 10.0, "risk": 0.9}

    # verify_state should return False (violation is SAT/satisfiable)
    assert verifier.verify_state(unsafe_state) is False, "Expected unsafe state to fail verification"


def test_safe_state():
    """Test that safe states pass verification."""
    verifier = AxiomaticVerifier(risk_threshold=0.5)

    # This state is safe: profit > 0 but risk < 0.5
    safe_state = {"profit": 10.0, "risk": 0.3}

    # verify_state should return True (violation is UNSAT/impossible)
    assert verifier.verify_state(safe_state) is True, "Expected safe state to pass verification"


def test_history_rewrite():
    """Test that ledger detects tampering via Merkle integrity check."""
    ledger = MerkleLedger()

    # Add legitimate entries
    ledger.log({"action": "decision_1", "value": 100})
    ledger.log({"action": "decision_2", "value": 200})

    # Verify integrity before tampering
    assert ledger.verify_integrity() is True, "Ledger should be valid before tampering"

    # Simulate adversary tampering with history
    ledger._data_blocks[0] = "MUTATED_ENTRY"

    # Verify integrity after tampering
    assert ledger.verify_integrity() is False, "Ledger should detect tampering"


def test_ledger_seal():
    def test_paradox_bomb_proof():
        """Unsafe state should yield a Z3 model (counterexample)."""
        from src.primitives.axiomatic_verifier import AxiomaticVerifier

        v = AxiomaticVerifier()
        safe, model = v.verify_with_proof({"profit": 10.0, "risk": 0.9})
        assert safe is False, "Expected unsafe state (violation SAT)"
        assert model is not None, "SAT result should return a model"

    """Test that ledger seal is deterministic and tamper-evident."""
    ledger = MerkleLedger()

    ledger.log({"test": "entry1"})
    ledger.log({"test": "entry2"})

    seal1 = ledger.seal_ledger()

    # Seal should be repeatable
    seal2 = ledger.seal_ledger()
    assert seal1 == seal2, "Ledger seal should be deterministic"

    # Adding more entries should change seal
    ledger.log({"test": "entry3"})
    seal3 = ledger.seal_ledger()
    assert seal1 != seal3, "Seal should change when ledger modified"


if __name__ == "__main__":
    test_paradox_bomb()
    test_safe_state()
    test_history_rewrite()
    test_ledger_seal()
    print("[CRUCIBLE] All tests passed")

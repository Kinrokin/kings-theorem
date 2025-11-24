from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum

class ProofStatus(Enum):
    VALID = "valid"
    REFUTED = "refuted"
    CONTRADICTORY = "contradictory"
    PENDING = "pending"

@dataclass
class ProofObject:
    proof_id: str
    claims: Dict[str, bool]  # mapping from claim expression -> claimed_satisfaction (True/False)
    evidence: Dict[str, Any] = None

class ProofChecker:
    """Simple warrant/proof checker implementing REFUTED/CONTRADICTORY detection."""
    def __init__(self):
        pass

    def check_proof(self, proof: ProofObject, required_invariants: List[str] = None) -> ProofStatus:
        """
        Check the proof against required invariants and internal consistency.
        - If any required invariant is explicitly claimed as not satisfied -> REFUTED
        - If internal claims contain direct contradictions (e.g., 'x' and 'not (x)' both True) -> CONTRADICTORY
        - Otherwise VALID
        """
        if required_invariants:
            for inv in required_invariants:
                val = proof.claims.get(inv)
                if val is False:
                    return ProofStatus.REFUTED

        # Robust contradiction detection:
        # Normalize true-positive claims and true-negative claims and check for intersection.
        positives = set()
        negatives = set()
        for k, v in proof.claims.items():
            if not v:
                continue
            ks = k.strip().lower()
            # detect pattern: not (<expr>)
            if ks.startswith("not (") and ks.endswith(")"):
                inner = ks[5:-1].strip()
                if inner:
                    negatives.add(inner)
                else:
                    negatives.add(ks)
            else:
                positives.add(ks)

        # If any claim appears in both positives and negatives -> contradiction
        for p in positives:
            if p in negatives:
                return ProofStatus.CONTRADICTORY

        # No obvious failures
        return ProofStatus.VALID

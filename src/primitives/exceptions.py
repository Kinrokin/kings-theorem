"""
AID: /src/primitives/exceptions.py
Proof ID: PRF-SIT-001
Axiom: Axiom 3 (Auditability)
Purpose: Centralized definition for the Standardized Infeasibility Token.
"""


class StandardizedInfeasibilityToken(Exception):
    """
    The SIT is NOT a crash. It is a formal proof of non-compliance.
    Used by the Student Kernel to signal that the 'Gold Standard' cannot be met.
    """

    pass


class SecurityError(Exception):
    """Raised when a security or governance invariant is violated during
    runtime or instantiation of sensitive components.
    """

    pass


class LedgerInvariantError(Exception):
    """Raised when ledger state mutation violates formal invariants:
    - Monotonicity (no removal of committed entries)
    - Uniqueness (no duplicate problem IDs)
    - Immutability (no in-place modification of finalized records)
    """

    pass

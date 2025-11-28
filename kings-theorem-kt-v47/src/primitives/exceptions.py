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

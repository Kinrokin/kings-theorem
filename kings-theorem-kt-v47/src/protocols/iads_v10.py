"""
AID: /src/protocols/iads_v10.py
Proof ID: PRF-IADS-010
Axiom: Axiom 5: Truth Maintenance
Purpose: Information Asymmetry Detection System.
"""


def detect_asymmetry(source_a: float, source_b: float, tolerance: float = 0.05) -> bool:
    """
    Detects if two data sources (which should be identical) have diverged.
    True = Asymmetry Detected (Danger).
    """
    delta = abs(source_a - source_b)
    return delta > tolerance

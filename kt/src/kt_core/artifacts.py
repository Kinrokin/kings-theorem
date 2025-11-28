"""Artifact types for King's Theorem proofs."""

from typing import Literal

ProofStatus = Literal[
    "PENDING",
    "GENERATING",
    "VERIFYING",
    "PROVEN",
    "REFUTED",
    "HALTED_BUDGET",
    "ERROR",
]
"""
Proof status enumeration:

- PENDING: Not yet started
- GENERATING: Prover generating candidate steps
- VERIFYING: Verifier checking step validity
- PROVEN: Proof successfully completed
- REFUTED: Proof found to be contradictory
- HALTED_BUDGET: Stopped due to resource exhaustion
- ERROR: Stopped due to runtime error
"""

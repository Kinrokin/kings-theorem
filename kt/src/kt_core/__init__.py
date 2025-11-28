"""
King's Theorem Core - Neuro-Symbolic Orchestrator
Phoenix Edition v6.0.0

A production-ready theorem proving engine that separates:
- Prover (creative/LLM - high entropy)
- Verifier (logical/symbolic - zero entropy)
- Supervisor (meta-cognitive - risk management)
"""

from .artifacts import ProofStatus
from .context import LogicStatement, ProofContext, ProofTrace
from .orchestrator import Orchestrator
from .prover import IProver, LLMProver
from .risk import RiskBudget
from .telemetry import Telemetry
from .verifier import IVerifier, Z3Verifier

__version__ = "6.0.0"
__all__ = [
    "ProofStatus",
    "LogicStatement",
    "ProofTrace",
    "ProofContext",
    "Orchestrator",
    "IProver",
    "LLMProver",
    "RiskBudget",
    "Telemetry",
    "IVerifier",
    "Z3Verifier",
]

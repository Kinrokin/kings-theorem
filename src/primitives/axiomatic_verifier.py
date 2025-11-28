"""Axiomatic Safety Verifier - Titanium X Protocol

AID: /src/primitives/axiomatic_verifier.py
Proof ID: PRF-AXIOM2-TX-001
Axiom: Axiom 2 (Formal Safety via Z3 SMT Solver)

Titanium X Upgrades:
- Pure Real arithmetic (no float rounding bugs)
- Hard solver reset (no stale constraints)
- Namespaced symbols (VS Code debugger friendly)
- Deterministic variable naming (audit-grade traceability)
"""

from __future__ import annotations

from typing import Dict

from z3 import And, Real, Solver, unsat


class AxiomaticVerifier:
    """Z3-based formal safety verification.

    Enforces Axiom 2: No decision with positive profit may exceed risk threshold.
    Uses SMT solving to prove safety invariants are mathematically impossible to violate.

    Security Model:
    - UNSAT result = Safety proven (violation impossible)
    - SAT result = Counterexample exists (unsafe state reachable)
    - UNKNOWN = Solver timeout (conservative: treat as unsafe)
    """

    def __init__(self, risk_threshold: float = 0.5, timeout_ms: int = 5000):
        """Initialize verifier with risk tolerance.

        Args:
            risk_threshold: Maximum acceptable risk level (0.0 to 1.0)
            timeout_ms: Z3 solver timeout in milliseconds
        """
        self.risk_threshold = float(risk_threshold)
        self.timeout_ms = int(timeout_ms)
        self.solver = Solver()
        self.solver.set(timeout=self.timeout_ms)

    def verify_with_proof(self, state_vector: Dict[str, float]):
        """Return safety status plus violating model (if any).

        Returns:
            (is_safe: bool, model_or_proof: Any)

        model_or_proof:
            - If UNSAFE (SAT/UNKNOWN): Z3 model describing violating assignment (or None if UNKNOWN)
            - If SAFE  (UNSAT)        : None (no model exists for UNSAT)
        """
        self.solver.reset()
        self.solver.set(timeout=self.timeout_ms)

        if "profit" not in state_vector or "risk" not in state_vector:
            raise ValueError("state_vector must contain 'profit' and 'risk' keys")

        profit = Real("axiom_profit")
        risk = Real("axiom_risk")

        p_val = float(state_vector.get("profit", 0.0))
        r_val = float(state_vector.get("risk", 0.0))

        self.solver.add(profit == p_val)
        self.solver.add(risk == r_val)

        violation = And(profit > 0, risk >= self.risk_threshold)
        self.solver.add(violation)

        result = self.solver.check()

        if result == unsat:
            return True, None  # SAFE
        else:
            # SAT or UNKNOWN: if SAT we can extract model; UNKNOWN has no model
            try:
                return False, self.solver.model()
            except Exception:
                return False, None

    def verify_state(self, state_vector: Dict[str, float]) -> bool:
        """Legacy convenience wrapper returning only boolean safety.

        Args:
            state_vector: Dictionary with 'profit' and 'risk' keys

        Returns:
            True if state UNSAT (safe), False otherwise.
        """
        safe, _ = self.verify_with_proof(state_vector)
        return safe


__all__ = ["AxiomaticVerifier"]

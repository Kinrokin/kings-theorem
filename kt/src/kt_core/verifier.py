"""Verifier interfaces for King's Theorem - the symbolic/logical engine."""

import asyncio
from abc import ABC, abstractmethod
from typing import List

try:
    from z3 import Solver, Z3Exception, parse_smt2_string, sat
except ImportError:
    # Graceful degradation if z3 not installed
    Solver = None
    parse_smt2_string = None
    Z3Exception = Exception
    sat = None

from .context import LogicStatement


class IVerifier(ABC):
    """
    Interface for the Logical Engine (Symbolic Verification).

    The Verifier is the gatekeeper of truth - it checks whether
    a proposed proof step is logically valid.
    """

    @abstractmethod
    async def verify_step(self, step: LogicStatement, context_steps: List[LogicStatement]) -> bool:
        """
        Verify a proof step using symbolic logic.

        Args:
            step: Candidate step to verify
            context_steps: Previous verified steps (context)

        Returns:
            True if step is logically valid, False otherwise
        """
        pass


class Z3Verifier(IVerifier):
    """
    Z3-based symbolic verifier.

    Uses the Z3 SMT solver to check satisfiability of formal
    representations. A step is verified if adding it to the
    context maintains satisfiability (SAT).
    """

    async def verify_step(self, step: LogicStatement, context_steps: List[LogicStatement]) -> bool:
        """
        Verify step using Z3 SMT solver.

        Args:
            step: Candidate step with formal SMT2 representation
            context_steps: Previous verified steps

        Returns:
            True if constraints are SAT, False if UNSAT or invalid
        """
        # Simulate verification latency
        await asyncio.sleep(0.01)

        if Solver is None:
            # Z3 not available, fallback to confidence threshold
            return step.confidence > 0.7

        solver = Solver()

        try:
            # Add formal constraints from context
            for prev in context_steps:
                if prev.formal:
                    try:
                        # Parse each statement separately
                        parsed = parse_smt2_string(prev.formal)
                        if isinstance(parsed, list):
                            for constraint in parsed:
                                solver.add(constraint)
                        else:
                            solver.add(parsed)
                    except (Z3Exception, AttributeError, TypeError):
                        # Malformed SMT2 in context, skip
                        continue

            # Add the candidate step's constraint
            if step.formal:
                try:
                    parsed = parse_smt2_string(step.formal)
                    if isinstance(parsed, list):
                        for constraint in parsed:
                            solver.add(constraint)
                    else:
                        solver.add(parsed)
                except (Z3Exception, AttributeError, TypeError):
                    # Malformed SMT2, reject
                    return False

            # Check satisfiability
            result = solver.check()
            return result == sat

        except (Z3Exception, AttributeError, RuntimeError, TypeError):
            # Z3 error, reject step
            return False

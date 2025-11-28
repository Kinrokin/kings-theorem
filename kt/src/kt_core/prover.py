"""Prover interfaces for King's Theorem - the creative/LLM engine."""

import asyncio
from abc import ABC, abstractmethod
from typing import List

from .context import LogicStatement


class IProver(ABC):
    """
    Interface for the Creative Engine (LLM/Generative).

    The Prover generates candidate proof steps that must be verified
    by the symbolic Verifier before acceptance.
    """

    @abstractmethod
    async def generate_step(self, context_steps: List[LogicStatement]) -> LogicStatement:
        """
        Generate a new proof step based on context.

        Args:
            context_steps: Previous verified steps in the proof

        Returns:
            Candidate LogicStatement (unverified)
        """
        pass


class LLMProver(IProver):
    """
    Mock LLM Prover implementation.

    In production, this connects to actual LLM APIs (OpenAI, Anthropic, etc.)
    For now, generates deterministic mock steps for testing.
    """

    async def generate_step(self, context_steps: List[LogicStatement]) -> LogicStatement:
        """
        Generate a mock proof step.

        Args:
            context_steps: Previous verified steps

        Returns:
            Mock LogicStatement with deterministic content
        """
        # Simulate LLM latency
        await asyncio.sleep(0.05)

        step_num = len(context_steps)

        # Generate deterministic mock content
        content = f"Derived step {step_num} from {len(context_steps)} premises."

        # Simple SMT2 constraint (note: full SMT2 requires proper context)
        # For production, use Z3 Python API or generate complete SMT2 with context
        formal = f"(declare-fun x{step_num} () Int)\n(assert (> x{step_num} 0))"

        return LogicStatement.new(
            content=content,
            formal=formal,
            source="llm_stub",
            confidence=0.85,
        )

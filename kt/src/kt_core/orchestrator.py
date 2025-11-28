"""Orchestrator - the central nervous system of King's Theorem."""

from typing import List, Optional, Tuple

from .artifacts import ProofStatus
from .context import LogicStatement, ProofContext, ProofTrace
from .prover import IProver
from .risk import RiskBudget
from .telemetry import Telemetry
from .verifier import IVerifier


class Orchestrator:
    """
    The central nervous system - manages interplay between Prover and Verifier.

    Orchestrates:
    - Generation of candidate proof steps (Prover)
    - Verification of steps (Verifier)
    - Risk budget enforcement (RiskBudget)
    - Backtracking on rejections
    - Status transitions and telemetry
    """

    def __init__(
        self,
        prover: IProver,
        verifier: IVerifier,
        telemetry: Optional[Telemetry] = None,
        max_rejections: int = 10,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            prover: Proof step generator
            verifier: Symbolic verifier
            telemetry: Telemetry bus (optional)
            max_rejections: Max consecutive rejections before backtrack
        """
        self.prover = prover
        self.verifier = verifier
        self.telemetry = telemetry or Telemetry(fields={})
        self.max_rejections = max_rejections

        self.status: ProofStatus = "PENDING"
        self.trace = ProofTrace()
        self.context_steps: List[LogicStatement] = []
        self.rejections: int = 0

    async def solve(self, theorem: str, budget: RiskBudget) -> Tuple[ProofStatus, ProofTrace]:
        """
        Attempt to prove a theorem.

        Args:
            theorem: Statement to prove
            budget: Resource constraints

        Returns:
            Tuple of (final status, proof trace)
        """
        self.status = "GENERATING"
        self.telemetry.event("status_change", status=self.status, theorem=theorem)

        # Seed with axiom
        axiom = LogicStatement.new(content=theorem, formal=None, source="axiom", confidence=1.0)
        self.context_steps.append(axiom)
        self.trace.add(axiom)
        _ctx = ProofContext(goal=theorem)

        # Main proof loop
        while budget.check():
            budget.consume(depth_inc=1, tokens=100)

            # GENERATION PHASE
            try:
                step = await self.prover.generate_step(self.context_steps)
            except Exception as e:
                self.status = "ERROR"
                self.telemetry.event("prover_error", error=str(e))
                return self.status, self.trace

            # VERIFICATION PHASE
            self.status = "VERIFYING"
            self.telemetry.event("status_change", status=self.status)

            try:
                ok = await self.verifier.verify_step(step, self.context_steps)
            except Exception as e:
                self.status = "ERROR"
                self.telemetry.event("verifier_error", error=str(e))
                return self.status, self.trace

            if ok:
                # Step verified - collapse wave function
                self.rejections = 0
                verified_step = LogicStatement.new(
                    content=step.content,
                    formal=step.formal,
                    source=step.source,
                    confidence=1.0,
                )
                self.context_steps.append(verified_step)
                self.trace.add(verified_step)
                self.telemetry.event("verified_step", id=verified_step.id)

                # Simple stopping rule: enough steps
                if len(self.context_steps) >= 5:
                    self.status = "PROVEN"
                    self.telemetry.event("status_change", status=self.status)
                    return self.status, self.trace
            else:
                # Step rejected
                self.rejections += 1
                self.telemetry.event("rejected_step", content=step.content, count=self.rejections)

                # Backtracking threshold
                if self.rejections >= self.max_rejections:
                    # Drop last non-axiom step if any
                    if len(self.context_steps) > 1:
                        dropped = self.context_steps.pop()
                        self.telemetry.event("backtrack", dropped=dropped.id)

                    # Halt after backtrack to prevent infinite loop
                    self.status = "HALTED_BUDGET"
                    self.telemetry.event("status_change", status=self.status)
                    return self.status, self.trace

        # Budget exhausted
        if self.status not in ("PROVEN", "ERROR"):
            self.status = "HALTED_BUDGET"
            self.telemetry.event("budget_halt", tokens=budget.tokens_used, depth=budget.current_depth)
            self.telemetry.event("status_change", status=self.status)

        return self.status, self.trace

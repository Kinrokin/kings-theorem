"""Temporal Verifier for Multi-Step Governance Reasoning

Extends Phase 3 RollingVerifier with bounded liveness, safety invariants,
and multi-step dependency checks for sequential governance contracts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class TemporalConstraint:
    """Defines a temporal invariant enforced across multi-step traces."""

    name: str
    min_steps: int = 1
    max_steps: int = 20
    required_phases: List[str] = field(default_factory=list)
    forbidden_sequences: List[tuple[str, str]] = field(default_factory=list)
    liveness_requirement: str | None = None


class TemporalVerifier:
    """Verifies multi-step governance sequences for safety + liveness."""

    def __init__(self, max_depth: int = 30):
        self.max_depth = max_depth
        self.constraints: List[TemporalConstraint] = []

    def add_constraint(self, constraint: TemporalConstraint) -> None:
        self.constraints.append(constraint)

    def verify_trace(self, trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check temporal invariants over the full trace.

        Returns:
            {
                "valid": bool,
                "violations": List[str],
                "constraint_results": Dict[str, bool]
            }
        """

        if len(trace) > self.max_depth:
            return {
                "valid": False,
                "violations": [f"Trace exceeds max depth ({len(trace)} > {self.max_depth})"],
                "constraint_results": {},
            }

        violations = []
        constraint_results = {}

        for constraint in self.constraints:
            result = self._check_constraint(trace, constraint)
            constraint_results[constraint.name] = result["valid"]
            if not result["valid"]:
                violations.extend(result["violations"])

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "constraint_results": constraint_results,
        }

    def _check_constraint(
        self,
        trace: List[Dict[str, Any]],
        constraint: TemporalConstraint,
    ) -> Dict[str, Any]:
        """Evaluate a single temporal constraint against the trace."""

        violations = []

        # 1. Bounded depth
        if not (constraint.min_steps <= len(trace) <= constraint.max_steps):
            violations.append(
                f"{constraint.name}: Trace length {len(trace)} outside bounds [{constraint.min_steps}, {constraint.max_steps}]"
            )

        # 2. Required phases present
        phases_seen = {event.get("phase") for event in trace}
        for required in constraint.required_phases:
            if required not in phases_seen:
                violations.append(f"{constraint.name}: Missing required phase '{required}'")

        # 3. Forbidden sequences
        for i in range(len(trace) - 1):
            phase_a = trace[i].get("phase")
            phase_b = trace[i + 1].get("phase")
            if (phase_a, phase_b) in constraint.forbidden_sequences:
                violations.append(f"{constraint.name}: Forbidden sequence ({phase_a} → {phase_b}) at step {i}")

        # 4. Liveness check (eventual settlement)
        if constraint.liveness_requirement:
            final_statuses = {event.get("status") for event in trace}
            if constraint.liveness_requirement not in final_statuses:
                violations.append(
                    f"{constraint.name}: Liveness requirement '{constraint.liveness_requirement}' not met"
                )

        return {"valid": len(violations) == 0, "violations": violations}


# Default multi-step governance constraint
def default_governance_constraint() -> TemporalConstraint:
    return TemporalConstraint(
        name="MultiStepGovernance",
        min_steps=3,
        max_steps=20,
        required_phases=["GUARDRAIL", "TRIGOVERNOR", "BROKER"],
        forbidden_sequences=[
            ("TIER_5_HALT", "EXECUTE"),
            ("HALT", "COMMITTED"),
        ],
        liveness_requirement="ESCROWED",
    )

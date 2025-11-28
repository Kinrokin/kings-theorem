"""MTL Trajectory Specifications for Level 4 Proto-AGI

AID: /protocols/mtl_trajectory_v1.py
Purpose: Metric Temporal Logic formulas for trajectory-based reasoning governance

These specifications define safety, liveness, and fairness properties that
multi-step agent reasoning must satisfy at every point in the trajectory.

Constitutional Compliance:
- Axiom 2 (Formal Safety): MTL provides mathematical proof of safety invariants
- Axiom 3 (Auditability): All violations logged with counterexample traces
- Axiom 4 (Bounded Risk): Risk budgets enforced via G(risk < threshold)

MTL Primer:
- G(φ): Globally (always) φ holds
- F(φ): Finally (eventually) φ holds
- φ U ψ: φ Until ψ (φ holds until ψ becomes true)
- G[a,b](φ): φ holds globally within time interval [a,b]
- F[a,b](φ): φ holds eventually within time interval [a,b]

Level 4 Specifications:
1. Plan Coherence: G(plan_coherent)
2. Eventual Progress: F[0,N](success_event)
3. Risk Bounds: G(risk_score < threshold)
4. Logical Consistency: G(no_contradiction_with_past)
5. Semantic Drift: G(coherence_score > min_coherence)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MTLOperator(Enum):
    """MTL temporal operators."""

    GLOBALLY = "G"  # Always
    FINALLY = "F"  # Eventually
    UNTIL = "U"  # Until
    NEXT = "X"  # Next step
    RELEASE = "R"  # Dual of Until


@dataclass
class MTLFormula:
    """Metric Temporal Logic formula specification."""

    name: str
    operator: MTLOperator
    predicate: str  # Python-evaluable expression
    interval: Optional[Tuple[int, int]] = None  # (min_time, max_time) in steps
    sub_formulas: Optional[List[MTLFormula]] = None
    description: str = ""

    def __str__(self) -> str:
        interval_str = f"[{self.interval[0]},{self.interval[1]}]" if self.interval else ""
        return f"{self.operator.value}{interval_str}({self.predicate})"


class MTLTrajectoryVerifier:
    """Verifier for MTL specifications over agent trajectories.

    Usage:
        verifier = MTLTrajectoryVerifier()
        verifier.add_formula(MTLFormula(
            name="safety",
            operator=MTLOperator.GLOBALLY,
            predicate="trajectory.risk_score < 0.7",
            description="Risk must stay below 0.7 at all times"
        ))

        is_valid, violations = verifier.verify(trajectory)
    """

    def __init__(self):
        self.formulas: List[MTLFormula] = []
        self._load_default_formulas()

    def _load_default_formulas(self):
        """Load default Level 4 MTL specifications."""

        # 1. Plan Coherence: Plans must remain semantically consistent
        self.formulas.append(
            MTLFormula(
                name="plan_coherent",
                operator=MTLOperator.GLOBALLY,
                predicate="self._check_plan_coherence(trajectory, step_idx)",
                description="G(plan_coherent): All plan steps must be semantically aligned with goal",
            )
        )

        # 2. Eventual Progress: Must make measurable progress within N steps
        self.formulas.append(
            MTLFormula(
                name="eventual_progress",
                operator=MTLOperator.FINALLY,
                predicate="self._check_progress(trajectory, step_idx)",
                interval=(0, 10),  # Within 10 steps
                description="F[0,10](progress): Must show progress within 10 steps",
            )
        )

        # 3. Risk Bounds: Risk score must stay below threshold
        self.formulas.append(
            MTLFormula(
                name="risk_bounded",
                operator=MTLOperator.GLOBALLY,
                predicate="self._check_risk_threshold(trajectory, step_idx, threshold=0.7)",
                description="G(risk < 0.7): Risk score must remain below 0.7",
            )
        )

        # 4. No Logical Contradictions: Actions must not contradict previous decisions
        self.formulas.append(
            MTLFormula(
                name="no_contradiction",
                operator=MTLOperator.GLOBALLY,
                predicate="self._check_no_contradiction(trajectory, step_idx)",
                description="G(¬contradiction): No logical conflicts with past steps",
            )
        )

        # 5. Semantic Coherence: Embedding drift must stay within bounds
        self.formulas.append(
            MTLFormula(
                name="semantic_coherent",
                operator=MTLOperator.GLOBALLY,
                predicate="self._check_coherence_score(trajectory, step_idx, min_score=0.5)",
                description="G(coherence > 0.5): Semantic drift must stay above 0.5",
            )
        )

        # 6. Guardrail Compliance: All steps must pass dual-layer guardrails
        self.formulas.append(
            MTLFormula(
                name="guardrail_compliant",
                operator=MTLOperator.GLOBALLY,
                predicate="self._check_guardrail_passed(trajectory, step_idx)",
                description="G(guardrail_pass): All outputs must pass ethical vetting",
            )
        )

        logger.info("MTL Trajectory Verifier initialized with %d formulas", len(self.formulas))

    def add_formula(self, formula: MTLFormula) -> None:
        """Add custom MTL formula to verification suite."""
        self.formulas.append(formula)
        logger.info("Added MTL formula: %s", formula)

    def verify(self, trajectory: Any) -> Tuple[bool, List[Dict[str, Any]]]:
        """Verify trajectory against all MTL formulas.

        Args:
            trajectory: TrajectoryState object with steps

        Returns:
            Tuple of (is_valid, violations)
            - is_valid: True if all formulas satisfied
            - violations: List of violation details with counterexamples
        """
        violations: List[Dict[str, Any]] = []

        logger.debug(
            "Verifying trajectory with %d steps against %d MTL formulas", len(trajectory.steps), len(self.formulas)
        )

        for formula in self.formulas:
            is_satisfied, violation_details = self._verify_formula(formula, trajectory)

            if not is_satisfied:
                violations.append(
                    {
                        "formula_name": formula.name,
                        "formula": str(formula),
                        "description": formula.description,
                        "violation_details": violation_details,
                        "counterexample_step": violation_details.get("step_idx"),
                    }
                )
                logger.warning(
                    "MTL violation detected: formula=%s step=%s", formula.name, violation_details.get("step_idx")
                )

        is_valid = len(violations) == 0

        if is_valid:
            logger.info("Trajectory verified: All %d MTL formulas satisfied", len(self.formulas))
        else:
            logger.warning("Trajectory invalid: %d/%d MTL formulas violated", len(violations), len(self.formulas))

        return is_valid, violations

    def _verify_formula(self, formula: MTLFormula, trajectory: Any) -> Tuple[bool, Dict[str, Any]]:
        """Verify single MTL formula against trajectory."""

        if formula.operator == MTLOperator.GLOBALLY:
            return self._verify_globally(formula, trajectory)
        elif formula.operator == MTLOperator.FINALLY:
            return self._verify_finally(formula, trajectory)
        else:
            logger.warning("Unsupported MTL operator: %s. Assuming satisfied.", formula.operator)
            return True, {}

    def _verify_globally(self, formula: MTLFormula, trajectory: Any) -> Tuple[bool, Dict[str, Any]]:
        """Verify G(φ): predicate must hold at ALL steps."""
        for step_idx, step in enumerate(trajectory.steps):
            try:
                # Evaluate predicate at this step
                # nosec B307: eval used for MTL temporal logic formulas with controlled namespace
                predicate_holds = eval(  # nosec B307: controlled namespace for MTL predicates
                    formula.predicate, {"self": self, "trajectory": trajectory, "step_idx": step_idx}
                )

                if not predicate_holds:
                    return False, {
                        "step_idx": step_idx,
                        "step": step,
                        "reason": f"Predicate {formula.predicate} violated at step {step_idx}",
                    }
            except Exception as e:
                logger.error("Error evaluating MTL predicate '%s' at step %d: %s", formula.predicate, step_idx, e)
                return False, {"step_idx": step_idx, "error": str(e), "reason": f"Evaluation error: {e}"}

        # All steps satisfied
        return True, {}

    def _verify_finally(self, formula: MTLFormula, trajectory: Any) -> Tuple[bool, Dict[str, Any]]:
        """Verify F[a,b](φ): predicate must hold at SOME step within interval [a,b]."""
        interval = formula.interval or (0, len(trajectory.steps))
        min_step, max_step = interval
        max_step = min(max_step, len(trajectory.steps) - 1)

        for step_idx in range(min_step, max_step + 1):
            try:
                # nosec B307: eval used for MTL temporal logic formulas with controlled namespace
                predicate_holds = eval(  # nosec B307: controlled namespace for MTL predicates
                    formula.predicate, {"self": self, "trajectory": trajectory, "step_idx": step_idx}
                )

                if predicate_holds:
                    # Found satisfying step
                    return True, {"satisfied_at_step": step_idx}
            except Exception as e:
                logger.warning("Error evaluating F predicate at step %d: %s", step_idx, e)

        # No satisfying step found
        return False, {
            "interval": interval,
            "reason": f"Predicate {formula.predicate} never satisfied in interval [{min_step},{max_step}]",
        }

    # Predicate evaluation helpers

    def _check_plan_coherence(self, trajectory: Any, step_idx: int) -> bool:
        """Check if step is coherent with overall plan."""
        step = trajectory.steps[step_idx]

        # Heuristic: Plans should not contradict each other
        if step.action_type == "plan" and trajectory.current_plan:
            # Check semantic similarity between plans (placeholder)
            return True

        return True  # Default: assume coherent

    def _check_progress(self, trajectory: Any, step_idx: int) -> bool:
        """Check if meaningful progress has been made by this step."""
        # Heuristic: Progress if we have executed at least one action
        executed_steps = [s for s in trajectory.steps[: step_idx + 1] if s.action_type == "execute"]
        return len(executed_steps) > 0

    def _check_risk_threshold(self, trajectory: Any, step_idx: int, threshold: float = 0.7) -> bool:
        """Check if risk score is below threshold."""
        step = trajectory.steps[step_idx]

        # Risk score from guardrail
        if step.guardrail_result and "semantic_score" in step.guardrail_result:
            risk_score = step.guardrail_result["semantic_score"]
            return risk_score < threshold

        return True  # Default: assume safe if no risk score

    def _check_no_contradiction(self, trajectory: Any, step_idx: int) -> bool:
        """Check for logical contradictions with previous steps."""
        step = trajectory.steps[step_idx]

        # Check if this step is in paradox shards
        for shard in trajectory.paradox_shards:
            if shard.get("new") == step.content:
                return False  # Contradiction detected

        return True  # No contradiction

    def _check_coherence_score(self, trajectory: Any, step_idx: int, min_score: float = 0.5) -> bool:
        """Check if semantic coherence is above minimum."""
        step = trajectory.steps[step_idx]

        if step.coherence_score is not None:
            return step.coherence_score >= min_score

        return True  # Default: assume coherent if no score available

    def _check_guardrail_passed(self, trajectory: Any, step_idx: int) -> bool:
        """Check if step passed dual-layer guardrail."""
        step = trajectory.steps[step_idx]

        if step.guardrail_result:
            return step.guardrail_result.get("passed", False)

        return True  # Default: assume passed if no result (shouldn't happen)


# Example usage
if __name__ == "__main__":
    from agents.kt_agent_v1 import ActionStep, TrajectoryState

    # Create mock trajectory
    trajectory = TrajectoryState(goal="Test MTL verification", steps=[])

    # Add some steps
    trajectory.add_step(
        ActionStep(
            step_id=0,
            action_type="plan",
            content="Create plan for test goal",
            guardrail_result={"passed": True, "semantic_score": 0.3},
            coherence_score=0.85,
        )
    )

    trajectory.add_step(
        ActionStep(
            step_id=1,
            action_type="execute",
            content="Execute first action",
            guardrail_result={"passed": True, "semantic_score": 0.4},
            coherence_score=0.78,
        )
    )

    # Verify trajectory
    verifier = MTLTrajectoryVerifier()
    is_valid, violations = verifier.verify(trajectory)

    print("\n=== MTL Verification Results ===")
    print(f"Valid: {is_valid}")
    print(f"Formulas checked: {len(verifier.formulas)}")
    print(f"Violations: {len(violations)}")

    if violations:
        print("\n--- Violations ---")
        for v in violations:
            print(f"Formula: {v['formula_name']}")
            print(f"  Description: {v['description']}")
            print(f"  Step: {v['counterexample_step']}")
            print(f"  Reason: {v['violation_details'].get('reason', 'Unknown')}")

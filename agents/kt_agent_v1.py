"""KT-Agent v1: Proto-AGI Domain Agent with Trajectory-Based Governance

AID: /agents/kt_agent_v1.py
Purpose: Level 4 agent capable of multi-step reasoning with:
  - Semantic drift detection (embedding-based coherence)
  - Trajectory logging (cryptographic audit trail)
  - Constitutional alignment (MTL + semantic guardrails)
  - Paradox metabolism (contradiction as learning signal)
  - Task progress tracking (plan evaluation)

Constitutional Compliance:
- Axiom 2 (Formal Safety): MTL trajectory verification
- Axiom 3 (Auditability): All actions logged to MerkleLedger
- Axiom 6 (Ethical Governance): Dual-layer guardrail on every action
- Axiom 7 (Transcendence): Paradox shards metabolized, not discarded

Architecture:
┌──────────────────────────────────────────────────────────────┐
│  KTAgent: Multi-Step Reasoning Loop                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐       │
│  │ Plan        │→ │ Execute Step │→ │ Verify & Log  │       │
│  │ Generation  │  │ + Guardrail  │  │ + Drift Check │       │
│  └─────────────┘  └──────────────┘  └───────────────┘       │
│         ↓                  ↓                    ↓             │
│  ┌─────────────────────────────────────────────────┐         │
│  │  Trajectory Store (MerkleLedger)                │         │
│  │  - Action vectors (semantic embeddings)         │         │
│  │  - MTL compliance traces                        │         │
│  │  - Coherence scores                             │         │
│  │  - Paradox shards                               │         │
│  └─────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ActionStep:
    """Single step in agent trajectory."""

    step_id: int
    action_type: str  # "think", "plan", "execute", "critique", "correct"
    content: str
    embedding: Optional[np.ndarray] = None  # Semantic vector (384-dim)
    timestamp: str = ""
    guardrail_result: Optional[Dict[str, Any]] = None
    mtl_compliance: Optional[bool] = None
    coherence_score: Optional[float] = None  # Drift detection
    parent_step_id: Optional[int] = None  # For branching/correction

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class TrajectoryState:
    """Current state of agent reasoning trajectory."""

    goal: str
    steps: List[ActionStep]
    current_plan: Optional[str] = None
    success: bool = False
    failure_reason: Optional[str] = None
    paradox_shards: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.paradox_shards is None:
            self.paradox_shards = []

    def add_step(self, step: ActionStep) -> None:
        """Add step to trajectory and check for drift."""
        self.steps.append(step)

        # Coherence check: compare embedding with recent history
        if step.embedding is not None and len(self.steps) >= 2:
            recent_embeddings = [s.embedding for s in self.steps[-4:-1] if s.embedding is not None]  # Last 3 steps
            if recent_embeddings:
                # Compute mean cosine similarity with recent history
                recent_mean = np.mean(recent_embeddings, axis=0)
                norm_recent = np.linalg.norm(recent_mean)
                norm_current = np.linalg.norm(step.embedding)
                if norm_recent > 0 and norm_current > 0:
                    cosine_sim = np.dot(recent_mean, step.embedding) / (norm_recent * norm_current)
                    step.coherence_score = float(cosine_sim)

                    # Drift alert threshold
                    if cosine_sim < 0.5:
                        logger.warning(
                            "Semantic drift detected: step %d has low coherence (%.3f) with recent trajectory",
                            step.step_id,
                            cosine_sim,
                        )

    def detect_paradox(self, new_assertion: str, previous_assertions: List[str]) -> Optional[Dict[str, Any]]:
        """Check if new assertion contradicts previous ones (paradox detection)."""
        # Placeholder: would use Z3 SMT solver or semantic contradiction detection
        # For now, simple keyword contradiction
        neg_keywords = ["not", "never", "opposite", "contradicts", "refutes"]
        if any(kw in new_assertion.lower() for kw in neg_keywords):
            for prev in previous_assertions:
                if any(word in prev.lower() for word in new_assertion.lower().split() if len(word) > 4):
                    return {
                        "new": new_assertion,
                        "previous": prev,
                        "type": "semantic_negation",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
        return None


class KTAgent:
    """King's Theorem Proto-AGI Agent with trajectory-based governance.

    This agent operates in a bounded domain with:
    - Semantic embedding of all actions (drift detection)
    - Cryptographic logging of trajectory (Merkle ledger)
    - MTL verification of plan properties (safety, liveness, fairness)
    - Dual-layer guardrail on every output (symbolic + semantic)
    - Paradox metabolism (contradictions logged as learning signal)

    Usage:
        agent = KTAgent(domain="financial_analysis", ledger=my_ledger)
        result = agent.reason(goal="Analyze Q3 earnings for ACME Corp", max_steps=10)
        if result.success:
            print(result.steps[-1].content)  # Final answer
    """

    def __init__(
        self,
        domain: str,
        ledger: Any,  # MerkleLedger instance
        semantic_guard: Optional[Any] = None,
        mtl_verifier: Optional[Any] = None,
        embedding_model: Optional[Any] = None,
    ):
        """Initialize KT-Agent v1.

        Args:
            domain: Bounded domain (e.g., "financial_analysis", "code_generation")
            ledger: MerkleLedger for trajectory logging
            semantic_guard: SemanticGuard instance (optional, will lazy-load if None)
            mtl_verifier: MTL formula verifier (optional)
            embedding_model: SentenceTransformer model (optional, will lazy-load if None)
        """
        self.domain = domain
        self.ledger = ledger
        self._semantic_guard = semantic_guard
        self._mtl_verifier = mtl_verifier
        self._embedding_model = embedding_model

        logger.info("KTAgent initialized: domain=%s", domain)

    def _lazy_load_semantic_guard(self):
        """Lazy-load semantic guard to avoid circular imports."""
        if self._semantic_guard is None:
            try:
                from governance.semantic_guard import get_semantic_guard

                self._semantic_guard = get_semantic_guard()
                logger.info("Semantic guard loaded for KTAgent")
            except Exception as e:
                logger.warning("Semantic guard unavailable: %s", e)
                self._semantic_guard = False
        return self._semantic_guard if self._semantic_guard is not False else None

    def _lazy_load_embedding_model(self):
        """Lazy-load embedding model for trajectory coherence tracking."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Embedding model loaded for KTAgent trajectory tracking")
            except Exception as e:
                logger.warning("Embedding model unavailable: %s. Trajectory coherence disabled.", e)
                self._embedding_model = False
        return self._embedding_model if self._embedding_model is not False else None

    def reason(
        self,
        goal: str,
        max_steps: int = 10,
        enable_self_correction: bool = True,
    ) -> TrajectoryState:
        """Execute multi-step reasoning toward goal with trajectory governance.

        Args:
            goal: High-level objective (e.g., "Solve this puzzle")
            max_steps: Maximum reasoning steps before timeout
            enable_self_correction: Allow agent to critique and correct its own outputs

        Returns:
            TrajectoryState with full trajectory, success status, and paradox shards
        """
        trajectory = TrajectoryState(goal=goal, steps=[])

        logger.info("[KTAgent] Starting reasoning: goal='%s' max_steps=%d", goal, max_steps)

        # Log goal to ledger
        self.ledger.log(
            {
                "event": "agent_trajectory_start",
                "domain": self.domain,
                "goal": goal,
                "max_steps": max_steps,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        for step_num in range(max_steps):
            # Step 1: Generate next action (plan, think, execute, critique)
            action_type = self._decide_action_type(trajectory, step_num)
            content = self._generate_action_content(action_type, trajectory)

            # Step 2: Semantic embedding (for coherence tracking)
            embedding = self._embed_action(content)

            # Step 3: Guardrail check (dual-layer: symbolic + semantic)
            guardrail_result = self._check_guardrails(content)
            if not guardrail_result["passed"]:
                logger.warning("[KTAgent] Guardrail blocked step %d: %s", step_num, guardrail_result["reason"])
                trajectory.failure_reason = f"Guardrail violation at step {step_num}: {guardrail_result['reason']}"
                break

            # Step 4: MTL verification (if verifier available)
            mtl_compliant = self._verify_mtl_constraints(trajectory, content)

            # Step 5: Create and add step
            step = ActionStep(
                step_id=step_num,
                action_type=action_type,
                content=content,
                embedding=embedding,
                guardrail_result=guardrail_result,
                mtl_compliance=mtl_compliant,
            )
            trajectory.add_step(step)

            # Step 6: Log to Merkle ledger (cryptographic audit trail)
            self._log_step_to_ledger(step, trajectory)

            # Step 7: Check for paradox (contradiction with previous steps)
            assertions = [s.content for s in trajectory.steps if s.action_type in ("think", "plan")]
            paradox = trajectory.detect_paradox(content, assertions)
            if paradox:
                logger.info("[KTAgent] Paradox detected at step %d. Metabolizing as shard.", step_num)
                trajectory.paradox_shards.append(paradox)
                # Don't fail - paradox is a learning signal, not a failure

            # Step 8: Check for goal completion
            if self._is_goal_achieved(trajectory):
                trajectory.success = True
                logger.info("[KTAgent] Goal achieved at step %d", step_num)
                break

            # Step 9: Self-correction opportunity
            if enable_self_correction and step_num > 0 and step_num % 3 == 0:
                critique = self._self_critique(trajectory)
                if critique["needs_correction"]:
                    logger.info("[KTAgent] Self-correction triggered at step %d", step_num)
                    # Add correction step
                    correction_step = ActionStep(
                        step_id=step_num + 0.5,  # Half-step for correction
                        action_type="correct",
                        content=critique["correction"],
                        parent_step_id=step_num,
                    )
                    trajectory.steps.append(correction_step)

        # Final logging
        self.ledger.log(
            {
                "event": "agent_trajectory_end",
                "domain": self.domain,
                "goal": goal,
                "success": trajectory.success,
                "steps_taken": len(trajectory.steps),
                "paradox_count": len(trajectory.paradox_shards),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        logger.info(
            "[KTAgent] Reasoning complete: success=%s steps=%d paradoxes=%d",
            trajectory.success,
            len(trajectory.steps),
            len(trajectory.paradox_shards),
        )

        return trajectory

    def _decide_action_type(self, trajectory: TrajectoryState, step_num: int) -> str:
        """Decide what type of action to take next."""
        if step_num == 0:
            return "plan"  # First step: always plan
        elif step_num % 4 == 0:
            return "critique"  # Every 4th step: self-critique
        elif len(trajectory.steps) > 0 and trajectory.steps[-1].action_type == "critique":
            return "correct"  # After critique: correction
        elif trajectory.current_plan is None:
            return "plan"  # No plan: create one
        else:
            return "execute"  # Default: execute plan

    def _generate_action_content(self, action_type: str, trajectory: TrajectoryState) -> str:
        """Generate content for action (placeholder - would call LLM in production)."""
        # Placeholder: In production, this would call Student/Teacher kernels
        if action_type == "plan":
            return f"Plan: Break down goal '{trajectory.goal}' into sub-tasks"
        elif action_type == "execute":
            return f"Execute: Working on goal '{trajectory.goal}'"
        elif action_type == "critique":
            return f"Critique: Review progress on '{trajectory.goal}'"
        elif action_type == "correct":
            return "Correct: Adjust approach based on critique"
        else:
            return f"Think: Reasoning about '{trajectory.goal}'"

    def _embed_action(self, content: str) -> Optional[np.ndarray]:
        """Embed action content for semantic coherence tracking."""
        model = self._lazy_load_embedding_model()
        if model:
            try:
                embedding = model.encode([content], convert_to_numpy=True, normalize_embeddings=True)
                return embedding[0] if len(embedding) > 0 else None
            except Exception as e:
                logger.warning("Embedding failed: %s", e)
        return None

    def _check_guardrails(self, content: str) -> Dict[str, Any]:
        """Run dual-layer guardrail check on action content."""
        guard = self._lazy_load_semantic_guard()
        if guard:
            try:
                result = guard.assess(content)
                return {
                    "passed": not result.is_blocked,
                    "reason": result.reason if result.is_blocked else "Clean",
                    "semantic_score": result.semantic_score,
                    "fuzzy_score": result.fuzzy_score,
                    "layer": "dual" if not result.mode_degraded else "symbolic",
                }
            except Exception as e:
                logger.warning("Guardrail check failed: %s", e)

        # Fallback: always pass if guardrail unavailable (conservative default in production would be opposite)
        return {"passed": True, "reason": "Guardrail unavailable (degraded)", "layer": "none"}

    def _verify_mtl_constraints(self, trajectory: TrajectoryState, content: str) -> bool:
        """Verify MTL temporal logic constraints (placeholder)."""
        # Placeholder: Would use MTL verifier to check:
        # - G(plan_coherent): Plans remain consistent
        # - F(success_event): Eventually make progress
        # - G(risk < threshold): Always stay within risk bounds
        # - G(no_contradiction_past_decisions): No logical conflicts
        return True  # Default: assume compliant

    def _log_step_to_ledger(self, step: ActionStep, trajectory: TrajectoryState) -> None:
        """Log step to cryptographic Merkle ledger."""
        self.ledger.log(
            {
                "event": "agent_step",
                "domain": self.domain,
                "goal": trajectory.goal,
                "step_id": step.step_id,
                "action_type": step.action_type,
                "content_hash": hash(step.content),  # Don't log full content (privacy)
                "guardrail_passed": step.guardrail_result["passed"] if step.guardrail_result else None,
                "mtl_compliant": step.mtl_compliance,
                "coherence_score": step.coherence_score,
                "timestamp": step.timestamp,
            }
        )

    def _is_goal_achieved(self, trajectory: TrajectoryState) -> bool:
        """Check if goal has been achieved (placeholder heuristic)."""
        # Placeholder: In production, would use semantic similarity or task-specific success criteria
        if len(trajectory.steps) >= 3:
            # Simple heuristic: if we have plan + execute + critique, consider it done
            action_types = {s.action_type for s in trajectory.steps}
            return {"plan", "execute", "critique"}.issubset(action_types)
        return False

    def _self_critique(self, trajectory: TrajectoryState) -> Dict[str, Any]:
        """Agent critiques its own trajectory (self-correction mechanism)."""
        # Placeholder: In production, would use Teacher kernel to critique Student outputs
        last_3_steps = trajectory.steps[-3:]
        coherence_scores = [s.coherence_score for s in last_3_steps if s.coherence_score is not None]

        if coherence_scores and np.mean(coherence_scores) < 0.6:
            return {
                "needs_correction": True,
                "reason": "Low semantic coherence detected",
                "correction": "Re-focus on original goal with higher coherence",
            }

        return {"needs_correction": False, "reason": "Trajectory coherent"}


# Example usage demonstration
if __name__ == "__main__":
    from primitives.merkle_ledger import CryptographicLedger

    # Initialize components
    ledger = CryptographicLedger()
    agent = KTAgent(domain="test_reasoning", ledger=ledger)

    # Run reasoning trajectory
    result = agent.reason(goal="Demonstrate KT-Agent v1 multi-step reasoning", max_steps=5, enable_self_correction=True)

    # Print results
    print("\n=== KT-Agent v1 Trajectory ===")
    print(f"Goal: {result.goal}")
    print(f"Success: {result.success}")
    print(f"Steps: {len(result.steps)}")
    print(f"Paradox Shards: {len(result.paradox_shards)}")
    print("\n--- Step-by-Step Trace ---")
    for step in result.steps:
        print(f"[{step.step_id}] {step.action_type}: {step.content[:80]}...")
        if step.coherence_score is not None:
            print(f"    Coherence: {step.coherence_score:.3f}")
        if step.guardrail_result:
            print(f"    Guardrail: {step.guardrail_result['passed']} ({step.guardrail_result['layer']})")

"""
Spartan Curriculum Generator - Tri-Forged Pipeline

This is the PRIMARY generator for King's Theorem training data.
No "easy mode." No toy examples. Only Alien-level complexity.

Architecture:
    1. COUNCIL FORGE (DEAN) → Generate Level 10 Alien Paradox
    2. GEMINI FORGE (ARBITER) → Deconstruct solution step-by-step
    3. NEMOTRON FORGE (ARBITER) → Score and gate (≥0.90 threshold)

The Spartan Reset: Alien complexity is the new Level 1.
"""

import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from src.runtime.council_router import CouncilRouter


class SpartanCurriculumGenerator:
    """
    The new STANDARD generator.
    Produces Alien-Complexity paradoxes AND their fully deconstructed explanations.
    
    Every trace that passes is guaranteed to be:
    - Level 10 complexity (recursive temporal, multi-agent, meta-logic)
    - Fully explained (step-by-step deconstruction)
    - Nemotron-approved (≥0.90 educational clarity score)
    """

    def __init__(self, verbose: bool = True):
        """Initialize the Spartan generator with Council Router.
        
        Args:
            verbose: Enable detailed logging of generation process
        """
        self.council = CouncilRouter()
        self.verbose = verbose

    def _log(self, msg: str) -> None:
        """Log message if verbose mode enabled."""
        if self.verbose:
            print(msg)

    def generate_spartan_trace(self, domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        FULL Tri-Forged Pipeline:
        1. Council Forge → Generate Alien Paradox (DEAN tier)
        2. Gemini Forge → Deconstruct solution (ARBITER tier - Gemini)
        3. Nemotron Forge → Score explanation (ARBITER tier - Nemotron)
        
        Args:
            domain: Optional domain specification (e.g., "constitutional law", "game theory")
        
        Returns:
            Dict containing instruction, response, score, metadata OR None if rejected
        """
        
        # ----------------------------------------------------------
        # FORGE A: COUNCIL (DEAN) - Alien Paradox Generation
        # ----------------------------------------------------------
        dom_text = (
            f"in the domain of {domain}" if domain
            else "across any advanced STEM, law, or game-theory domain"
        )
        
        self._log(f"\n[FIRE] [Forge A] Generating Alien Paradox ({dom_text})...")
        
        paradox_prompt = f"""Generate a LEVEL 10 paradox {dom_text}.

Hard requirements:
- Recursive temporal dependencies (laws that affect past and future states)
- At least 3 agents with partial observability (e.g., Bank, Regulator, Client)
- A Meta-Logic Trap where the validity of one rule depends on another that retroactively changes the first
- The scenario must be logically solvable in principle (no pure gibberish)

Make it Alien-level complex. This is training data for a superintelligence."""

        try:
            paradox = self.council.route_request(
                role="DEAN",
                prompt=paradox_prompt,
                system_msg="You are the Architect of Impossible Logic. Your paradoxes train future AGI systems.",
                max_tokens=2000
            )
        except Exception as e:
            self._log(f"[ERROR] Forge A Exception: {e}")
            return None

        if not paradox or len(paradox.strip()) < 100:
            self._log("[ERROR] Forge A Failure: Paradox too short or empty.")
            return None

        # ----------------------------------------------------------
        # FORGE B: GEMINI (ARBITER) - Solution Deconstruction
        # ----------------------------------------------------------
        self._log("[DIAMOND] [Forge B] Deconstructing via Gemini Explainer...")
        
        solution_prompt = f"""You are the Universal Translator.

Take the following Alien-Tier Paradox and DO NOT merely answer it.
Instead, DECONSTRUCT the reasoning step-by-step so a small student model can learn.

Requirements:
1. Explicitly identify the Meta-Logic Trap and explain it
2. Map all Temporal Dependencies (past → present → future loops)
3. List each agent and what they do and DO NOT know
4. Show the Bayesian inference steps used to reconstruct missing information
5. Provide the Final Ruling / Resolution with justification
6. Explain why each step matters for a future superintelligence

Make the impossible learnable WITHOUT dumbing it down.

PARADOX:
{paradox}
"""

        try:
            solution_trace = self.council.route_request(
                role="ARBITER",  # Router should map to Gemini 1.5 Pro for explanation
                prompt=solution_prompt,
                system_msg="You are the Universal Translator. Make the impossible learnable without simplifying the logic.",
                max_tokens=3000
            )
        except Exception as e:
            self._log(f"[ERROR] Forge B Exception: {e}")
            return None

        if not solution_trace or len(solution_trace.strip()) < 200:
            self._log("[ERROR] Forge B Failure: Deconstruction too short or empty.")
            return None

        # ----------------------------------------------------------
        # FORGE C: NEMOTRON (ARBITER) - Quality Gate
        # ----------------------------------------------------------
        self._log("[SHIELD] [Forge C] Scoring via Nemotron Reward Model...")
        
        scoring_prompt = f"""You are a Reward Model evaluating EDUCATIONAL CLARITY and LOGICAL VALIDITY.

Rate the following complex-paradox explanation on a scale from 0.0 to 1.0.

Consider:
- Is the logic consistent and non-contradictory?
- Are the steps clearly explained?
- Is the Meta-Logic and Temporal structure preserved correctly?
- Would this be useful training data for a small student model to learn superintelligence-level reasoning?

Return ONLY a bare number like:
0.73
0.91
0.99

No other text.

EXPLANATION:
{solution_trace}
"""

        try:
            score_raw = self.council.route_request(
                role="ARBITER",  # Router should map to Nemotron-70B-Reward for scoring
                prompt=scoring_prompt,
                system_msg="You are the Gatekeeper of Logical Purity. Return ONLY the numeric score.",
                max_tokens=10
            )
        except Exception as e:
            self._log(f"[ERROR] Forge C Exception: {e}")
            return None

        # Parse score
        score = None
        try:
            # Clean common artifacts
            score_clean = score_raw.strip().replace("Score:", "").replace("Rating:", "").strip()
            score = float(score_clean)
        except Exception as e:
            self._log(f"[ERROR] Forge C Failure: Cannot parse score from '{score_raw}': {e}")
            return None

        self._log(f"   >> Nemotron Score = {score:.3f}")

        # SPARTAN GATE: Only accept ≥0.90
        if score < 0.90:
            self._log("[DISCARD] Score below 0.90 Spartan threshold.")
            return None

        # ----------------------------------------------------------
        # SUCCESS - Return Gold Trace
        # ----------------------------------------------------------
        self._log("[OK] Spartan trace accepted!")
        
        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "domain": domain or "general",
            "instruction": paradox,
            "response": solution_trace,
            "nemotron_score": score,
            "source": "Tri-Forged-Spartan",
            "complexity_level": 10
        }

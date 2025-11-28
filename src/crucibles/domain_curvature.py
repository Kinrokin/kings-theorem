#!/usr/bin/env python3
"""
Domain Curvature Generator - Non-Euclidean Paradox Seeds
Generates paradoxes with exotic geometric properties.
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.runtime.council_router import CouncilRouter


class DomainCurvatureGenerator:
    """
    Generates non-Euclidean paradox seeds with geometric curvature.
    
    Curvature types:
    - hyperbolic: Negative curvature, diverging logic paths
    - elliptic: Positive curvature, converging logic paths
    - parabolic: Zero curvature, parallel logic paths
    - retrocausal: Time-reversed causal structures
    """

    def __init__(
        self,
        verbose: bool = True,
        base_temperature: float = 1.1,
    ):
        """
        Initialize the Domain Curvature Generator.
        
        Args:
            verbose: Enable detailed logging
            base_temperature: Base temperature for generation
        """
        self.verbose = verbose
        self.base_temperature = base_temperature
        self.council = CouncilRouter()

    def _log(self, message: str) -> None:
        """Helper method for conditional logging."""
        if self.verbose:
            print(message)

    @staticmethod
    def detect_flattening(paradox: str) -> bool:
        """
        Detect if a curved paradox has flattened to Euclidean logic.
        
        Args:
            paradox: The paradox to check
            
        Returns:
            True if flattening detected, False otherwise
        """
        markers = [
            "linearizes",
            "reduces to classical logic",
            "flattens",
            "normalizes",
            "becomes euclidean",
            "classical resolution",
        ]
        return any(marker in paradox.lower() for marker in markers)

    def generate(
        self,
        domain: str,
        curvature_type: str,
        max_attempts: int = 3,
    ) -> Optional[str]:
        """
        Generate a curved paradox seed.
        
        Args:
            domain: Domain for the paradox
            curvature_type: Type of curvature (hyperbolic, elliptic, parabolic, retrocausal)
            max_attempts: Maximum generation attempts
            
        Returns:
            Paradox seed string or None on failure
        """
        # PHASE 4: Curvature-aware temperatures
        curvature_temp_map = {
            "hyperbolic": 1.10,
            "elliptic": 1.15,
            "parabolic": 1.20,
            "retrocausal": 1.30,
        }
        
        temp = curvature_temp_map.get(curvature_type, self.base_temperature)

        # Curvature-specific prompts
        curvature_prompts = {
            "hyperbolic": """Generate a paradox with HYPERBOLIC (negative) curvature.

Properties:
- Logic paths DIVERGE exponentially
- Multiple valid but contradictory resolutions exist
- The more you analyze, the more solutions appear
- Infinite interpretations in finite space

Example: A proof that simultaneously validates and invalidates itself through path divergence.

Domain: {domain}

Output ONLY the paradox. Make it concrete and unsolvable through flat logic.""",
            "elliptic": """Generate a paradox with ELLIPTIC (positive) curvature.

Properties:
- Logic paths CONVERGE to a singularity
- All reasoning loops back to the same contradiction
- Escape attempts circle back to origin
- Finite interpretations in bounded space

Example: A statement that, no matter how you approach it, always leads to the same impossible conclusion.

Domain: {domain}

Output ONLY the paradox. Make it concrete and loop-invariant.""",
            "parabolic": """Generate a paradox with PARABOLIC (zero) curvature.

Properties:
- Logic paths remain PARALLEL but never meet
- Multiple independent contradictions coexist
- No interaction between paradox layers
- Infinite non-interacting solutions

Example: Two completely separate paradoxes that share the same statement but never resolve each other.

Domain: {domain}

Output ONLY the paradox. Make it have parallel contradictions.""",
            "retrocausal": """Generate a paradox with RETROCAUSAL structure.

Properties:
- Effects precede causes
- Future states determine past logic
- Knowledge of the solution changes the problem
- Observer's conclusion alters the premise

Example: A paradox where knowing the answer makes the question impossible.

Domain: {domain}

Output ONLY the paradox. Make it temporally reversed.""",
        }

        prompt_template = curvature_prompts.get(curvature_type)
        if not prompt_template:
            self._log(f"⚠️  Unknown curvature type: {curvature_type}")
            return None

        prompt = prompt_template.format(domain=domain)
        
        system_msg = (
            f"You are a geometric logician. Generate {curvature_type} paradoxes "
            "that preserve non-Euclidean structure. Never flatten to classical logic."
        )

        # Retry loop with flattening detection
        for attempt in range(max_attempts):
            try:
                self._log(
                    f"   🌀 Generating {curvature_type} seed (attempt {attempt + 1}/{max_attempts})..."
                )

                response = self.council.route_request(
                    role="DEAN",
                    prompt=prompt,
                    system_msg=system_msg,
                    temperature=temp,
                )

                if not response or len(response.strip()) < 50:
                    self._log(f"   ⚠️  Insufficient content generated")
                    continue

                paradox = response.strip()

                # PHASE 5: Flattening detection
                if self.detect_flattening(paradox):
                    self._log(f"   ⚠️  Flattening detected, retrying...")
                    continue

                # Verify curvature preservation
                if curvature_type.lower() not in paradox.lower():
                    # Add explicit curvature marker if missing
                    paradox = f"[{curvature_type.upper()} CURVATURE]\n{paradox}"

                self._log(f"   ✅ {curvature_type} seed generated ({len(paradox)} chars)")
                return paradox

            except Exception as e:
                self._log(f"   ❌ Error generating {curvature_type} seed: {e}")
                continue

        self._log(f"   ❌ Failed to generate {curvature_type} seed after {max_attempts} attempts")
        return None

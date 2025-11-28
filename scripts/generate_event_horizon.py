#!/usr/bin/env python3
"""
Event Horizon v2 - Colostrum Refinery
A self-refining adversarial intelligence refinery for generating Level 12 paradoxes.

This system generates paradoxes, solves them, critiques solutions, and refines
via annealing until only the highest quality synthetic data passes the Nemotron gate.
"""

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.runtime.council_router import CouncilRouter


class EventHorizonGenerator:
    """
    The Colostrum Refinery - generates and refines Level 12 paradoxes
    through adversarial critique and thermal annealing.
    """

    def __init__(
        self,
        verbose: bool = True,
        max_rounds: int = 5,
        target_score: float = 0.99,
        min_acceptable_score: float = 0.95,
        initial_temperature: float = 1.1,
    ):
        """
        Initialize the Event Horizon Generator.

        Args:
            verbose: Enable detailed logging
            max_rounds: Maximum refinement iterations
            target_score: Score threshold to stop refinement
            min_acceptable_score: Minimum score to accept data
            initial_temperature: Starting temperature for generation
        """
        self.verbose = verbose
        self.max_rounds = max_rounds
        self.target_score = target_score
        self.min_acceptable_score = min_acceptable_score
        self.initial_temperature = initial_temperature
        self.council = CouncilRouter()

        if self.verbose:
            print(f"🌌 Event Horizon v2 Initialized")
            print(f"   Max Rounds: {max_rounds}")
            print(f"   Target Score: {target_score}")
            print(f"   Min Acceptable: {min_acceptable_score}")
            print(f"   Initial Temp: {initial_temperature}")

    def _log(self, message: str) -> None:
        """Helper method for conditional logging."""
        if self.verbose:
            print(message)

    def _parse_score(self, raw_response: str) -> float:
        """
        Robust score parser that handles multiple formats.
        
        Handles:
        - "0.95"
        - "Score: 0.95"
        - "0.95/1.0"
        - "The score is 0.92"
        
        Args:
            raw_response: Raw string from LLM
            
        Returns:
            Float score between 0.0 and 1.0, defaults to 0.0 on failure
        """
        if not raw_response:
            return 0.0

        try:
            # Try direct float conversion first
            return float(raw_response.strip())
        except ValueError:
            pass

        # Extract first decimal number using regex
        # Matches patterns like: 0.95, 0.9, .95
        pattern = r'(\d*\.?\d+)'
        matches = re.findall(pattern, raw_response)
        
        for match in matches:
            try:
                score = float(match)
                # Validate range
                if 0.0 <= score <= 1.0:
                    return score
                # Handle scores possibly out of 10
                elif 0.0 <= score <= 10.0:
                    return score / 10.0
            except ValueError:
                continue

        # If all parsing fails, return 0.0
        if self.verbose:
            print(f"⚠️  Failed to parse score from: {raw_response[:100]}")
        return 0.0

    def _generate_paradox(self, domain: str) -> Optional[str]:
        """
        Generate a Level 12 paradox using high-temperature DEAN.

        Args:
            domain: Domain/theme for the paradox

        Returns:
            Paradox string or None on failure
        """
        system_msg = (
            "You are the DEAN of Impossible Logic. Generate paradoxes that appear "
            "naive-impossible but are meta-logically solvable through recursive "
            "temporal dependencies and agent knowledge state evolution."
        )

        prompt = f"""Generate a Level 12 paradox in the domain of {domain}.

Requirements:
1. Must involve recursive temporal dependencies (time loops, causality violations)
2. Must involve evolving agent knowledge states (what the agent knows changes the solution)
3. Must appear impossible at first glance
4. Must be solvable through meta-logical reasoning

Output ONLY the paradox scenario. Make it concrete and specific."""

        try:
            response = self.council.route_request(
                role="DEAN",
                prompt=prompt,
                system_msg=system_msg,
                temperature=self.initial_temperature,
            )
            
            if response and len(response.strip()) > 50:
                return response.strip()
            else:
                if self.verbose:
                    print(f"⚠️  Paradox generation returned insufficient content")
                return None

        except Exception as e:
            if self.verbose:
                print(f"❌ Error generating paradox: {e}")
            return None

    def _initial_deconstruction(self, paradox: str) -> Optional[str]:
        """
        Deconstruct the paradox into strict teachable logic.

        Args:
            paradox: The paradox to deconstruct

        Returns:
            Initial solution or None on failure
        """
        system_msg = (
            "You are the ARBITER. You deconstruct impossible logic into strict, "
            "teachable reasoning. Map agent knowledge states and temporal dependencies explicitly."
        )

        prompt = f"""Deconstruct this paradox into a strict logical solution:

{paradox}

Requirements:
1. Identify the recursive temporal structure
2. Map agent knowledge states at each time step
3. Explain how the paradox resolves through meta-logic
4. Use precise notation where helpful
5. Make it teachable - another AI should be able to replicate this reasoning

Provide a complete, rigorous solution."""

        try:
            response = self.council.route_request(
                role="ARBITER",
                prompt=prompt,
                system_msg=system_msg,
                temperature=0.3,
            )

            if response and len(response.strip()) > 100:
                return response.strip()
            else:
                if self.verbose:
                    print(f"⚠️  Deconstruction returned insufficient content")
                return None

        except Exception as e:
            if self.verbose:
                print(f"❌ Error in deconstruction: {e}")
            return None

    def _score_solution(self, solution: str) -> float:
        """
        Score a solution using NEMOTRON strict judgment.

        Args:
            solution: The solution to score

        Returns:
            Score between 0.0 and 1.0
        """
        system_msg = (
            "You are NEMOTRON, the final arbiter of quality. You judge solutions "
            "with absolute precision. Output ONLY a numerical score."
        )

        prompt = f"""Score this solution on a scale of 0.0 to 1.0.

Solution:
{solution}

Criteria:
- Logical rigor: Is the reasoning airtight?
- Completeness: Are all aspects addressed?
- Teachability: Can another system learn from this?
- Notation clarity: Is the formalism precise?

Output ONLY a decimal number between 0.0 and 1.0. Nothing else."""

        try:
            response = self.council.route_request(
                role="NEMOTRON",
                prompt=prompt,
                system_msg=system_msg,
                temperature=0.1,
            )

            score = self._parse_score(response)
            return score

        except Exception as e:
            if self.verbose:
                print(f"❌ Error scoring solution: {e}")
            return 0.0

    def _criticize_solution(self, solution: str, score: float) -> Optional[str]:
        """
        Generate hostile peer review critique of the solution.

        Args:
            solution: Solution to critique
            score: Current score

        Returns:
            Critique string or None on failure
        """
        system_msg = (
            "You are a CRITIC - a hostile peer reviewer. Your job is to find flaws, "
            "ambiguities, and weaknesses. Be specific and merciless. Do NOT rewrite "
            "the solution, only identify problems."
        )

        prompt = f"""Critique this solution (current score: {score:.2f}):

{solution}

Identify:
1. Logical gaps or unstated assumptions
2. Ambiguous notation or terminology
3. Missing edge cases
4. Areas where reasoning could be more rigorous
5. Any inconsistencies

Be specific. Point to exact problems. Do NOT provide solutions, only critique."""

        try:
            response = self.council.route_request(
                role="CRITIC",
                prompt=prompt,
                system_msg=system_msg,
                temperature=0.4,
            )

            if response and len(response.strip()) > 20:
                return response.strip()
            else:
                if self.verbose:
                    print(f"⚠️  Critique returned insufficient content")
                return None

        except Exception as e:
            if self.verbose:
                print(f"❌ Error generating critique: {e}")
            return None

    def _improve_solution(
        self,
        paradox: str,
        old_solution: str,
        critique: str,
        temperature: float,
    ) -> Optional[str]:
        """
        Improve the solution based on critique using competitive DEAN.

        Args:
            paradox: Original paradox
            old_solution: Previous solution attempt
            critique: Critique of the old solution
            temperature: Current temperature for generation

        Returns:
            Improved solution or None on failure
        """
        system_msg = (
            "You are the DEAN competing against your previous self. "
            "You must WIN by producing a superior solution that addresses all critiques."
        )

        prompt = f"""You previously attempted to solve this paradox, but your solution was critiqued.

PARADOX:
{paradox}

YOUR PREVIOUS SOLUTION:
{old_solution}

CRITIQUE:
{critique}

Your task: Produce an IMPROVED solution that:
1. Addresses every point in the critique
2. Maintains logical rigor
3. Is more complete and teachable
4. Uses clearer notation

This is a competition against your past self. WIN."""

        try:
            response = self.council.route_request(
                role="DEAN",
                prompt=prompt,
                system_msg=system_msg,
                temperature=temperature,
            )

            if response and len(response.strip()) > 100:
                return response.strip()
            else:
                if self.verbose:
                    print(f"⚠️  Improvement returned insufficient content")
                return None

        except Exception as e:
            if self.verbose:
                print(f"❌ Error improving solution: {e}")
            return None

    def _compress_solution(self, solution: str) -> Optional[str]:
        """
        Compress solution into dense "Neutron Star" format.

        Args:
            solution: Verbose solution

        Returns:
            Compressed solution or None on failure
        """
        system_msg = (
            "You are the ARBITER performing Neutron Star compression. "
            "Convert explanations into maximally dense notation and pseudo-mathematics."
        )

        prompt = f"""Compress this solution into ~500 tokens of dense notation.

VERBOSE SOLUTION:
{solution}

Requirements:
1. Use symbolic notation where possible
2. Remove all redundancy
3. Maintain complete logical content
4. Use pseudo-mathematical formalism
5. Think: textbook theorem proof, not blog post

Output the compressed form ONLY."""

        try:
            response = self.council.route_request(
                role="ARBITER",
                prompt=prompt,
                system_msg=system_msg,
                temperature=0.3,
            )

            if response and len(response.strip()) > 50:
                return response.strip()
            else:
                if self.verbose:
                    print(f"⚠️  Compression returned insufficient content")
                return None

        except Exception as e:
            if self.verbose:
                print(f"❌ Error compressing solution: {e}")
            return None

    def _fractal_refinement_loop(
        self,
        paradox: str,
        initial_solution: str,
    ) -> Tuple[str, float, int]:
        """
        The core refinement engine using adversarial critique and annealing.

        Args:
            paradox: The paradox being solved
            initial_solution: Starting solution

        Returns:
            Tuple of (best_solution, best_score, rounds_used)
        """
        best_solution = initial_solution
        best_score = self._score_solution(initial_solution)
        round_idx = 0

        if self.verbose:
            print(f"\n🔥 Entering Fractal Refinement Loop")
            print(f"   Initial Score: {best_score:.3f}")

        for round_idx in range(self.max_rounds):
            if self.verbose:
                print(f"\n   🔄 Round {round_idx + 1}/{self.max_rounds}")

            # Check if we've reached the target
            if best_score >= self.target_score:
                if self.verbose:
                    print(f"   ✅ Target score {self.target_score} reached!")
                break

            # Generate critique
            critique = self._criticize_solution(best_solution, best_score)
            if not critique:
                if self.verbose:
                    print(f"   ⚠️  Critique failed, skipping round")
                continue

            # Calculate annealed temperature
            temperature = max(
                0.1,  # Hard floor to prevent zero/negative
                self.initial_temperature - (0.1 * round_idx)
            )

            if self.verbose:
                print(f"   🌡️  Temperature: {temperature:.2f}")

            # Generate improved solution
            improved_solution = self._improve_solution(
                paradox=paradox,
                old_solution=best_solution,
                critique=critique,
                temperature=temperature,
            )

            if not improved_solution:
                if self.verbose:
                    print(f"   ⚠️  Improvement failed, keeping previous solution")
                continue

            # Score the improved solution
            new_score = self._score_solution(improved_solution)

            if self.verbose:
                print(f"   📊 New Score: {new_score:.3f} (prev: {best_score:.3f})")

            # Update best if improved
            if new_score > best_score:
                best_solution = improved_solution
                best_score = new_score
                if self.verbose:
                    print(f"   ⬆️  Solution improved!")
            else:
                if self.verbose:
                    print(f"   ➡️  No improvement, keeping previous")

        return best_solution, best_score, round_idx + 1

    def mine_singularity(
        self,
        domain: str,
        sample_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Complete pipeline: generate, refine, gate, compress.

        Args:
            domain: Domain for paradox generation
            sample_id: Unique identifier for this sample

        Returns:
            Dictionary with complete sample data or None if rejected
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"🌌 Mining Singularity #{sample_id} - Domain: {domain}")
            print(f"{'='*60}")

        # Phase 1: Generate Paradox
        if self.verbose:
            print(f"\n📝 Phase 1: Generating Paradox...")
        
        paradox = self._generate_paradox(domain)
        if not paradox:
            if self.verbose:
                print(f"❌ Paradox generation failed")
            return None

        if self.verbose:
            print(f"✅ Paradox generated ({len(paradox)} chars)")

        # Phase 2: Initial Deconstruction
        if self.verbose:
            print(f"\n🔍 Phase 2: Initial Deconstruction...")

        initial_solution = self._initial_deconstruction(paradox)
        if not initial_solution:
            if self.verbose:
                print(f"❌ Initial deconstruction failed")
            return None

        if self.verbose:
            print(f"✅ Initial solution generated ({len(initial_solution)} chars)")

        # Phase 3: Fractal Refinement Loop
        if self.verbose:
            print(f"\n🌀 Phase 3: Fractal Refinement...")

        final_solution, final_score, rounds_used = self._fractal_refinement_loop(
            paradox=paradox,
            initial_solution=initial_solution,
        )

        if self.verbose:
            print(f"\n✅ Refinement complete: {rounds_used} rounds, score {final_score:.3f}")

        # Phase 4: The Gate - Quality Check
        if final_score < self.min_acceptable_score:
            if self.verbose:
                print(f"\n🚫 REJECTED: Score {final_score:.3f} < {self.min_acceptable_score}")
                print(f"   This sample will not pollute the dataset.")
            return None

        if self.verbose:
            print(f"\n✅ PASSED GATE: Score {final_score:.3f} >= {self.min_acceptable_score}")

        # Phase 5: Compression
        if self.verbose:
            print(f"\n🗜️  Phase 5: Neutron Star Compression...")

        compressed_solution = self._compress_solution(final_solution)
        if not compressed_solution:
            if self.verbose:
                print(f"⚠️  Compression failed, using verbose version")
            compressed_solution = final_solution

        if self.verbose:
            print(f"✅ Compression complete ({len(compressed_solution)} chars)")

        # Build final sample
        sample = {
            "id": f"eh_v2_{sample_id:06d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": domain,
            "instruction": paradox,
            "response_verbose": final_solution,
            "response_compressed": compressed_solution,
            "score": final_score,
            "rounds": rounds_used,
            "metadata": {
                "initial_temperature": self.initial_temperature,
                "max_rounds": self.max_rounds,
                "target_score": self.target_score,
            }
        }

        if self.verbose:
            print(f"\n✨ Singularity #{sample_id} successfully mined!")

        return sample

    def mine_singularity_from_seed(
        self,
        domain: str,
        paradox_seed: str,
        curvature_type: str = "N/A",
    ) -> Optional[Dict[str, Any]]:
        """
        Mine a singularity from a pre-generated paradox seed (curved or euclidean).
        
        Args:
            domain: Domain of the paradox
            paradox_seed: Pre-generated paradox to refine
            curvature_type: Type of curvature (hyperbolic, elliptic, etc.)
            
        Returns:
            Dictionary with complete sample data or None if rejected
        """
        self._log(f"\n🌀 [Curved Seed] Initiating Refinement from {curvature_type} seed...")
        paradox = paradox_seed

        current_solution = self._initial_deconstruction(paradox)
        if not current_solution:
            self._log("❌ Failed to produce initial deconstruction from seed.")
            return None

        best_solution, best_score, rounds = self._fractal_refinement_loop(
            paradox, current_solution
        )

        if best_score < self.min_acceptable_score:
            self._log(
                f"🗑️ Final score {best_score:.3f} below minimum acceptable. Discarding."
            )
            return None

        compressed = self._compress_solution(best_solution)
        if not compressed:
            compressed = best_solution

        # PHASE 6: Metadata preservation for curvature
        curvature_preserved = (
            "hyperbolic" in paradox.lower()
            or "elliptic" in paradox.lower()
            or "parabolic" in paradox.lower()
            or "retrocausal" in paradox.lower()
        )

        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": domain,
            "instruction": paradox,
            "response_verbose": best_solution,
            "response_compressed": compressed,
            "refinement_rounds": rounds,
            "final_score": best_score,
            "source": f"Curved_Horizon_Refinement_{curvature_type}",
            "curvature_preserved": curvature_preserved,
        }


def run_harvest(
    count: int,
    out_path: str,
    domain: str = "temporal_logic",
    verbose: bool = True,
    max_rounds: int = 5,
    target_score: float = 0.99,
    min_acceptable_score: float = 0.95,
    initial_temperature: float = 1.1,
):
    """
    Harvest multiple singularity samples.

    Args:
        count: Number of accepted samples to generate
        out_path: Output .jsonl file path
        domain: Domain for paradox generation
        verbose: Enable detailed logging
        max_rounds: Maximum refinement rounds per sample
        target_score: Target score for early stopping
        min_acceptable_score: Minimum score to accept
        initial_temperature: Initial generation temperature
    """
    generator = EventHorizonGenerator(
        verbose=verbose,
        max_rounds=max_rounds,
        target_score=target_score,
        min_acceptable_score=min_acceptable_score,
        initial_temperature=initial_temperature,
    )

    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    accepted_count = 0
    attempt_count = 0
    rejected_count = 0

    print(f"\n{'='*60}")
    print(f"🌌 EVENT HORIZON V2 - COLOSTRUM REFINERY")
    print(f"{'='*60}")
    print(f"Target: {count} accepted samples")
    print(f"Domain: {domain}")
    print(f"Output: {out_path}")
    print(f"{'='*60}\n")

    # Open file in append mode for crash safety
    with open(output_path, 'a', encoding='utf-8') as f:
        while accepted_count < count:
            attempt_count += 1

            print(f"\n{'='*60}")
            print(f"Attempt {attempt_count} | Accepted: {accepted_count}/{count} | Rejected: {rejected_count}")
            print(f"{'='*60}")

            # Mine a singularity
            sample = generator.mine_singularity(
                domain=domain,
                sample_id=accepted_count + 1,
            )

            if sample is None:
                rejected_count += 1
                if verbose:
                    print(f"\n❌ Sample rejected (total rejected: {rejected_count})")
                continue

            # Write immediately for crash safety
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
            f.flush()  # Force write to disk

            accepted_count += 1

            if verbose:
                print(f"\n✅ Sample {accepted_count}/{count} written to disk")

    # Final report
    print(f"\n{'='*60}")
    print(f"🎉 HARVEST COMPLETE")
    print(f"{'='*60}")
    print(f"Accepted: {accepted_count}")
    print(f"Rejected: {rejected_count}")
    print(f"Total Attempts: {attempt_count}")
    print(f"Success Rate: {accepted_count / attempt_count * 100:.1f}%")
    print(f"Output: {output_path.absolute()}")
    print(f"{'='*60}\n")


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Event Horizon v2 - Colostrum Refinery for Level 12 Paradoxes"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of accepted samples to generate (default: 10)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/event_horizon_v2.jsonl",
        help="Output .jsonl file path (default: data/event_horizon_v2.jsonl)",
    )

    parser.add_argument(
        "--domain",
        type=str,
        default="temporal_logic",
        help="Domain for paradox generation (default: temporal_logic)",
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="Maximum refinement rounds per sample (default: 5)",
    )

    parser.add_argument(
        "--target-score",
        type=float,
        default=0.99,
        help="Target score for early stopping (default: 0.99)",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=0.95,
        help="Minimum acceptable score (default: 0.95)",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=1.1,
        help="Initial generation temperature (default: 1.1)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose output",
    )

    args = parser.parse_args()

    run_harvest(
        count=args.count,
        out_path=args.output,
        domain=args.domain,
        verbose=not args.quiet,
        max_rounds=args.max_rounds,
        target_score=args.target_score,
        min_acceptable_score=args.min_score,
        initial_temperature=args.temperature,
    )


if __name__ == "__main__":
    main()

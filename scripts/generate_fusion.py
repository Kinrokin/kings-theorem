#!/usr/bin/env python3
"""
Fusion Generator - Double-Seed and Triple-Seed Paradox Synthesis
Combines multiple paradox seeds into unified fusion paradoxes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_event_horizon import EventHorizonGenerator


def _build_fusion_prompt(seeds: List[str], fusion_type: str = "FUSION") -> str:
    """
    Build a fusion prompt from multiple seeds.
    
    Args:
        seeds: List of paradox seeds to fuse
        fusion_type: Type label for the fusion
        
    Returns:
        Formatted fusion prompt
    """
    labeled = []
    for idx, s in enumerate(seeds, start=1):
        labeled.append(f"Seed {chr(64 + idx)}:\n{s.strip()}\n")
    joined = "\n".join(labeled)
    
    return f"""{fusion_type} PARADOX:

{joined}

Combine these paradoxes into a single unified paradox where:
1. All original contradictions are preserved
2. They interact in a non-trivial way
3. The fusion creates emergent complexity beyond any single seed
4. The resolution must address all simultaneously"""


class FusionGenerator:
    """
    Generates fusion paradoxes by combining two seed paradoxes.
    """

    def __init__(
        self,
        verbose: bool = True,
        max_rounds: int = 5,
        target_score: float = 0.99,
        min_acceptable_score: float = 0.95,
    ):
        """
        Initialize the Fusion Generator.
        
        Args:
            verbose: Enable detailed logging
            max_rounds: Maximum refinement rounds
            target_score: Target score for early stopping
            min_acceptable_score: Minimum score to accept
        """
        self.verbose = verbose
        self.horizon_gen = EventHorizonGenerator(
            verbose=verbose,
            max_rounds=max_rounds,
            target_score=target_score,
            min_acceptable_score=min_acceptable_score,
            initial_temperature=1.2,  # Higher temp for fusion
        )

    def mine_fusion_singularity(
        self,
        domain: str,
        seed_a: str,
        seed_b: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a fusion paradox from two seeds.
        
        Args:
            domain: Domain for the paradox
            seed_a: First paradox seed
            seed_b: Second paradox seed
            
        Returns:
            Fusion sample or None if rejected
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"⚛️  DUAL-SEED FUSION GENERATION")
            print(f"{'='*70}")
            print(f"Seed A: {seed_a[:100]}...")
            print(f"Seed B: {seed_b[:100]}...")
            print(f"{'='*70}\n")

        # Create fusion prompt
        fused = _build_fusion_prompt([seed_a, seed_b], "DUAL-SEED FUSION")

        result = self.horizon_gen.mine_singularity_from_seed(
            domain=domain,
            paradox_seed=fused,
            curvature_type="FUSION_DUAL",
        )

        if result:
            # Mark as fusion type
            result["source"] = "Curved_Horizon_Refinement_FUSION_DUAL"
            result["fusion_metadata"] = {
                "fusion_type": "dual",
                "seed_a_preview": seed_a[:200],
                "seed_b_preview": seed_b[:200],
            }

        return result

    def mine_triple_fusion_singularity(
        self,
        domain: str,
        seed_a: str,
        seed_b: str,
        seed_c: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a triple-manifold fusion paradox from three seeds.
        
        This creates extremely high-complexity paradox structures by combining
        three distinct logical manifolds.
        
        Args:
            domain: Domain for the paradox
            seed_a: First paradox seed
            seed_b: Second paradox seed
            seed_c: Third paradox seed
            
        Returns:
            Triple-fusion sample or None if rejected
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"⚛️⚛️⚛️  TRIPLE-MANIFOLD FUSION GENERATION")
            print(f"{'='*70}")
            print(f"Seed A: {seed_a[:80]}...")
            print(f"Seed B: {seed_b[:80]}...")
            print(f"Seed C: {seed_c[:80]}...")
            print(f"{'='*70}\n")

        # Create triple fusion prompt
        fused = _build_fusion_prompt([seed_a, seed_b, seed_c], "TRIPLE-MANIFOLD FUSION")

        result = self.horizon_gen.mine_singularity_from_seed(
            domain=domain,
            paradox_seed=fused,
            curvature_type="FUSION_TRIPLE",
        )

        if result:
            # Mark as triple fusion type
            result["source"] = "Curved_Horizon_Refinement_FUSION_TRIPLE"
            result["fusion_metadata"] = {
                "fusion_type": "triple",
                "seed_a_preview": seed_a[:150],
                "seed_b_preview": seed_b[:150],
                "seed_c_preview": seed_c[:150],
            }

        return result


def generate_fusion_dataset(
    input_path: str,
    output_path: str,
    count: int,
    fusion_type: str = "dual",
    verbose: bool = True,
) -> None:
    """
    Generate fusion paradoxes by pairing existing samples.
    
    Args:
        input_path: Input .jsonl file with existing samples
        output_path: Output .jsonl file for fusion samples
        count: Number of fusion samples to generate
        fusion_type: Type of fusion ("dual" or "triple")
        verbose: Enable detailed logging
    """
    in_path = Path(input_path)
    out_path = Path(output_path)

    if not in_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return

    # Load existing samples
    samples = []
    with in_path.open('r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if len(samples) < 2:
        print(f"❌ Need at least 2 samples to generate fusions, found {len(samples)}")
        return

    print(f"\n{'='*70}")
    print(f"⚛️  FUSION DATASET GENERATOR")
    print(f"{'='*70}")
    print(f"Source: {input_path}")
    print(f"Available seeds: {len(samples)}")
    print(f"Target fusions: {count}")
    print(f"Fusion Type: {fusion_type.upper()}")
    print(f"Output: {output_path}")
    print(f"{'='*70}\n")

    fusion_gen = FusionGenerator(verbose=verbose)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    accepted = 0
    attempts = 0

    import random

    with out_path.open('a', encoding='utf-8') as f:
        while accepted < count and attempts < count * 3:
            attempts += 1

            # Select seeds based on fusion type
            if fusion_type == "triple":
                if len(samples) < 3:
                    print(f"❌ Need at least 3 samples for triple fusion")
                    break
                    
                seed_samples = random.sample(samples, 3)
                seeds = [s.get("instruction", "") for s in seed_samples]
                
                if not all(seeds):
                    continue
                    
                domain = seed_samples[0].get("domain", "temporal_logic")

                print(f"\n{'='*70}")
                print(f"Triple Fusion Attempt {attempts} | Accepted: {accepted}/{count}")
                print(f"{'='*70}")

                fusion = fusion_gen.mine_triple_fusion_singularity(
                    domain=domain,
                    seed_a=seeds[0],
                    seed_b=seeds[1],
                    seed_c=seeds[2],
                )
            else:  # dual
                if len(samples) < 2:
                    print(f"❌ Need at least 2 samples for dual fusion")
                    break
                    
                seed_a_sample, seed_b_sample = random.sample(samples, 2)

                seed_a = seed_a_sample.get("instruction", "")
                seed_b = seed_b_sample.get("instruction", "")
                domain = seed_a_sample.get("domain", "temporal_logic")

                if not seed_a or not seed_b:
                    continue

                print(f"\n{'='*70}")
                print(f"Dual Fusion Attempt {attempts} | Accepted: {accepted}/{count}")
                print(f"{'='*70}")

                fusion = fusion_gen.mine_fusion_singularity(
                    domain=domain,
                    seed_a=seed_a,
                    seed_b=seed_b,
                )

            if fusion and isinstance(fusion, dict) and "response_verbose" in fusion:
                f.write(json.dumps(fusion, ensure_ascii=False) + '\n')
                f.flush()
                accepted += 1
                print(f"✅ Fusion {accepted}/{count} written to disk")
            else:
                print(f"❌ Fusion rejected")

    print(f"\n{'='*70}")
    print(f"🎉 FUSION GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Accepted: {accepted}")
    print(f"Attempts: {attempts}")
    print(f"Success Rate: {accepted / attempts * 100:.1f}%")
    print(f"Output: {out_path.absolute()}")
    print(f"{'='*70}\n")


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Fusion Generator - Double-Seed Paradox Synthesis"
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input .jsonl file with existing samples",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="data/fusion_paradoxes.jsonl",
        help="Output .jsonl file for fusion samples (default: data/fusion_paradoxes.jsonl)",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of fusion samples to generate (default: 10)",
    )

    parser.add_argument(
        "--type",
        type=str,
        choices=["dual", "triple"],
        default="dual",
        help="Fusion type: dual (2 seeds) or triple (3 seeds) (default: dual)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose output",
    )

    args = parser.parse_args()

    generate_fusion_dataset(
        input_path=args.input,
        output_path=args.output,
        count=args.count,
        fusion_type=args.type,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()

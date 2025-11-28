#!/usr/bin/env python3
"""
Curved Curriculum Runner - Ouroboros Protocol Phase 1
Generates synthetic data with geometric curvature and Euclidean baselines.
"""

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_event_horizon import EventHorizonGenerator
from src.crucibles.domain_curvature import DomainCurvatureGenerator


# PHASE 2 FIX 1: Curvature type definitions
CURVATURE_TYPES: List[str] = ["hyperbolic", "elliptic", "parabolic", "retrocausal"]


def run_curved_curriculum(
    count: int,
    output_path: str,
    domain: str = "temporal_logic",
    curved_ratio: float = 0.5,
    verbose: bool = True,
    max_rounds: int = 5,
    target_score: float = 0.99,
    min_acceptable_score: float = 0.95,
) -> None:
    """
    Generate a curriculum mixing curved and Euclidean paradoxes.
    
    Args:
        count: Total number of accepted samples to generate
        output_path: Output .jsonl file path
        domain: Domain for paradox generation
        curved_ratio: Ratio of curved samples (0.0 = all Euclidean, 1.0 = all curved)
        verbose: Enable detailed logging
        max_rounds: Maximum refinement rounds per sample
        target_score: Target score for early stopping
        min_acceptable_score: Minimum score to accept
    """
    out = Path(output_path)
    
    # PHASE 2 FIX 3: Ensure output directory exists
    out.parent.mkdir(parents=True, exist_ok=True)

    # Initialize generators
    horizon_gen = EventHorizonGenerator(
        verbose=verbose,
        max_rounds=max_rounds,
        target_score=target_score,
        min_acceptable_score=min_acceptable_score,
        initial_temperature=1.1,
    )

    curvature_gen = DomainCurvatureGenerator(
        verbose=verbose,
        base_temperature=1.1,
    )

    # Calculate split
    curved_count = int(count * curved_ratio)
    euclidean_count = count - curved_count

    print(f"\n{'='*70}")
    print(f"🌀 CURVED CURRICULUM RUNNER - OUROBOROS PROTOCOL")
    print(f"{'='*70}")
    print(f"Target: {count} total samples")
    print(f"  • Curved: {curved_count} ({curved_ratio*100:.0f}%)")
    print(f"  • Euclidean: {euclidean_count} ({(1-curved_ratio)*100:.0f}%)")
    print(f"Domain: {domain}")
    print(f"Output: {output_path}")
    print(f"{'='*70}\n")

    accepted = 0
    attempts = 0
    rejected = 0
    
    # PHASE 2 FIX 5: Cap attempts
    max_attempts = count * 5

    # Track curved vs euclidean accepted
    curved_accepted = 0
    euclidean_accepted = 0

    # Open file in append mode for crash safety
    with out.open('a', encoding='utf-8') as f:
        while accepted < count and attempts < max_attempts:
            attempts += 1

            # Decide: curved or euclidean?
            need_curved = curved_accepted < curved_count
            need_euclidean = euclidean_accepted < euclidean_count

            if need_curved and need_euclidean:
                # Both needed, choose by ratio
                use_curved = (curved_accepted / max(1, curved_accepted + euclidean_accepted)) < curved_ratio
            elif need_curved:
                use_curved = True
            elif need_euclidean:
                use_curved = False
            else:
                break  # We're done

            print(f"\n{'='*70}")
            print(f"Attempt {attempts} | Accepted: {accepted}/{count} (C:{curved_accepted}, E:{euclidean_accepted}) | Rejected: {rejected}")
            print(f"{'='*70}")

            ex = None

            if use_curved:
                # Generate curved sample
                import random
                curvature_type = random.choice(CURVATURE_TYPES)
                
                print(f"🌀 Generating CURVED sample ({curvature_type})...")
                
                # Generate curved seed
                seed = curvature_gen.generate(
                    domain=domain,
                    curvature_type=curvature_type,
                    max_attempts=3,
                )

                if seed:
                    # Refine the curved seed
                    ex = horizon_gen.mine_singularity_from_seed(
                        domain=domain,
                        paradox_seed=seed,
                        curvature_type=curvature_type,
                    )
                else:
                    print(f"❌ Failed to generate {curvature_type} seed")

            else:
                # Generate Euclidean sample
                print(f"📐 Generating EUCLIDEAN sample...")
                
                ex = horizon_gen.mine_singularity(
                    domain=domain,
                    sample_id=accepted + 1,
                )

            # PHASE 3: Bug prevention checks
            if ex is None:
                rejected += 1
                print(f"❌ Sample rejected (None returned)")
                continue

            if not isinstance(ex, dict):
                rejected += 1
                print(f"❌ Sample rejected (not a dict)")
                continue

            if "response_verbose" not in ex:
                rejected += 1
                print(f"❌ Sample rejected (missing response_verbose)")
                continue

            if ex.get("final_score", 0) < min_acceptable_score:
                rejected += 1
                print(f"❌ Sample rejected (score {ex.get('final_score', 0):.3f} < {min_acceptable_score})")
                continue

            # PHASE 2 FIX 4: Ensure Unicode JSON writing works
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
            
            # PHASE 3: Flush after write
            f.flush()

            accepted += 1
            
            if use_curved:
                curved_accepted += 1
            else:
                euclidean_accepted += 1

            print(f"✅ Sample {accepted}/{count} written to disk")

    # PHASE 3: Check for zero samples
    if accepted == 0:
        raise RuntimeError(
            "No generated samples passed filters. Check generators and score thresholds."
        )

    # Final report
    print(f"\n{'='*70}")
    print(f"🎉 CURVED CURRICULUM COMPLETE")
    print(f"{'='*70}")
    print(f"Accepted: {accepted} ({curved_accepted} curved, {euclidean_accepted} euclidean)")
    print(f"Rejected: {rejected}")
    print(f"Total Attempts: {attempts}")
    print(f"Success Rate: {accepted / attempts * 100:.1f}%")
    print(f"Output: {out.absolute()}")
    print(f"{'='*70}\n")


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Curved Curriculum Runner - Ouroboros Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 samples (50% curved)
  python scripts/run_curved_curriculum.py --count 100

  # Generate 50 samples (80% curved)
  python scripts/run_curved_curriculum.py --count 50 --curved-ratio 0.8

  # Custom domain and output
  python scripts/run_curved_curriculum.py --count 20 --domain quantum_ethics --output data/quantum_curved.jsonl
        """
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
        default="data/curved_curriculum.jsonl",
        help="Output .jsonl file path (default: data/curved_curriculum.jsonl)",
    )

    parser.add_argument(
        "--domain",
        type=str,
        default="temporal_logic",
        help="Domain for paradox generation (default: temporal_logic)",
    )

    parser.add_argument(
        "--curved-ratio",
        type=float,
        default=0.5,
        help="Ratio of curved samples (0.0-1.0, default: 0.5)",
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
        "--quiet",
        action="store_true",
        help="Disable verbose output",
    )

    args = parser.parse_args()

    run_curved_curriculum(
        count=args.count,
        output_path=args.output,
        domain=args.domain,
        curved_ratio=args.curved_ratio,
        verbose=not args.quiet,
        max_rounds=args.max_rounds,
        target_score=args.target_score,
        min_acceptable_score=args.min_score,
    )


if __name__ == "__main__":
    main()

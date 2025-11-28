"""
Script: Spartan Curriculum Runner
Purpose: Generate Level 10 Alien-Complexity training data via Tri-Forged Pipeline.

The Spartan Reset:
    Alien complexity is the new Level 1.
    No toy examples. No easy mode. Only superintelligence-grade training data.

Pipeline:
    1. Council Forge (DEAN) → Generate Level 10 paradox
    2. Gemini Forge (ARBITER) → Deconstruct step-by-step
    3. Nemotron Forge (ARBITER) → Score and gate (≥0.90)

This replaces the old 3-example toy curriculum with dynamic multi-domain generation
across 350+ domains using all 15 Council models.
"""
import json
import logging
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.curriculum.spartan_curriculum import SpartanCurriculum

logger = logging.getLogger(__name__)

def run_spartan_curriculum(steps: int, output_path: str) -> None:
    """
    Execute Spartan Curriculum generation pipeline.
    
    Generates N training examples using the Tri-Forged Pipeline:
    - Council generates Level 10 paradoxes
    - Gemini deconstructs solutions
    - Nemotron scores and gates (≥0.90)
    
    Args:
        steps: Number of Spartan examples to generate
        output_path: JSONL file path for output dataset
    """
    logger.info("=" * 80)
    logger.info("SPARTAN CURRICULUM RUNNER - Tri-Forged Pipeline")
    logger.info("=" * 80)
    logger.info(f"Target: {steps} Level 10 Spartan training examples")
    logger.info(f"Output: {output_path}")
    logger.info(f"Quality Gate: Nemotron >=0.90 threshold")
    logger.info("=" * 80)
    
    # Initialize Spartan Curriculum
    try:
        curriculum = SpartanCurriculum(verbose=True)
    except Exception as e:
        logger.error(f"[FATAL] Failed to initialize Spartan Curriculum: {e}")
        raise
    
    # Generate Spartan batch
    logger.info("\n[GENERATION START]\n")
    dataset = curriculum.generate_batch(steps)
    
    # Save to JSONL
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\n[SAVE] Writing {len(dataset)} examples to {output_path}")
    with out_path.open("w", encoding="utf-8") as f:
        for entry in dataset:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # Final report
    stats = curriculum.get_statistics()
    logger.info("\n" + "=" * 80)
    logger.info("SPARTAN RUN COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Accepted: {stats['accepted']} / Target: {steps}")
    logger.info(f"Rejected: {stats['rejected']}")
    logger.info(f"Success Rate: {stats['success_rate']:.1%}")
    logger.info(f"Domains Covered: {stats['domains_used']}")
    logger.info(f"Output: {output_path}")
    logger.info("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Spartan Curriculum Generator - Tri-Forged Pipeline for Level 10 Training Data"
    )
    parser.add_argument(
        "--steps", 
        type=int, 
        default=50, 
        help="Number of Spartan examples to generate (default: 50)"
    )
    parser.add_argument(
        "--out", 
        type=str, 
        default="data/golden_spartan_dataset.jsonl",
        help="Output JSONL file path (default: data/golden_spartan_dataset.jsonl)"
    )
    args = parser.parse_args()

    # Setup logging
    try:
        from src.logging_config import setup_logging
        setup_logging()
    except Exception:
        logging.basicConfig(
            level=logging.INFO, 
            format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s"
        )
    
    # Run Spartan curriculum
    run_spartan_curriculum(steps=args.steps, output_path=args.out)
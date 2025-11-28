"""KT Intelligence Factory: Batch Crucible Generator

Generates training data for the KT curriculum with reproducible seeding
and difficulty-aware complexity gradients.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crucibles.spec import DIFFICULTY_BANDS, CrucibleGenerator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KT Intelligence Factory: Generate Training Crucibles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate full curriculum (D1-D7, 10 each)
  python scripts/generate_crucibles.py --count 10

  # Generate only D7 monsters for stress testing
  python scripts/generate_crucibles.py --level 7 --count 50

  # Reproducible generation for CI/CD
  python scripts/generate_crucibles.py --seed 42 --count 5
        """,
    )
    parser.add_argument("--level", type=int, help="Specific difficulty level (1-7)")
    parser.add_argument("--count", type=int, default=10, help="Number of crucibles per level")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data/crucibles", help="Output directory")
    args = parser.parse_args()

    # Ensure output directory exists
    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    generator = CrucibleGenerator(seed=args.seed)

    levels_to_run = [args.level] if args.level else list(DIFFICULTY_BANDS.keys())

    print(f"🏭 Starting KT Crucible Factory (Seed: {args.seed})")

    total_generated = 0
    for level in levels_to_run:
        print(f"   -> Generating Level D{level} batch ({args.count} items)...")
        filename = out_path / f"kt_crucibles_d{level}.jsonl"

        with open(filename, "w", encoding="utf-8") as f:
            for i in range(args.count):
                spec = generator.generate(difficulty=level)
                f.write(json.dumps(spec.to_dict(), ensure_ascii=False) + "\n")
                total_generated += 1

        print(f"      ✅ Wrote {args.count} crucibles to {filename.name}")

    print(f"\n✅ Factory Complete. Generated {total_generated} crucibles in {out_path}")
    print(f"   Constitution specs included: {list(generator.constitution.get('specs', {}).keys())}")


if __name__ == "__main__":
    main()

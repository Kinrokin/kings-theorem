#!/usr/bin/env python3
"""
Ouroboros Runner - The Feedback God-Loop
Autonomous closed-loop optimizer for synthetic data generation.

Monitors:
- Contamination rates
- Curvature distribution health
- Composite reward signals

Auto-adjusts:
- Temperature schedule
- Curvature ratio
- Generation parameters

Regenerates batches until equilibrium is achieved.
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_curved_curriculum import run_curved_curriculum
from src.crucibles.reward import RewardComponents, RewardWeights, compute_reward


DATA_DIR = Path("data")
HARVEST_DIR = DATA_DIR / "harvests"
METRICS_DIR = DATA_DIR / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)
HARVEST_DIR.mkdir(parents=True, exist_ok=True)

OUROBOROS_LOG = METRICS_DIR / "ouroboros_log.jsonl"


@dataclass
class OuroborosConfig:
    """Configuration for Ouroboros optimization loop."""
    domain: str = "temporal_logic"
    initial_temp: float = 1.10
    curvature_ratio: float = 0.50
    batch_size: int = 20
    max_iterations: int = 5
    min_temp: float = 0.90
    max_temp: float = 1.30
    min_curvature_ratio: float = 0.05
    max_curvature_ratio: float = 0.80
    min_acceptable_score: float = 0.95
    target_reward: float = 0.85  # Stop early if reached


@dataclass
class IterationMetrics:
    """Metrics tracked per Ouroboros iteration."""
    iteration: int
    harvest_path: str
    contamination_rate: float
    compression_density: float
    fractal_score_gain: float
    drift_variance: float
    reward: float
    temperature: float
    curvature_ratio: float
    num_samples: int
    euclidean_count: int
    curved_count: int


def _safe_json_lines(path: Path) -> List[Dict[str, Any]]:
    """Safely load JSONL file, skipping malformed lines."""
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def compute_metrics_from_harvest(path: Path, min_score: float = 0.95) -> RewardComponents:
    """
    Compute reward components from a harvest JSONL file.

    Metrics:
    - contamination_rate: fraction missing critical fields or below min_score
    - compression_density: average ratio of compressed/verbose length
    - fractal_score_gain: average improvement over baseline (0.9)
    - drift_variance: placeholder for ontological drift (TODO: wire Tribunal)

    Args:
        path: Path to harvest JSONL file
        min_score: Minimum acceptable score threshold

    Returns:
        RewardComponents with computed metrics
    """
    rows = _safe_json_lines(path)
    if not rows:
        return RewardComponents(
            contamination_rate=1.0,
            compression_density=0.0,
            fractal_score_gain=0.0,
            drift_variance=1.0,
        )

    invalid = 0
    compression_ratios: List[float] = []
    score_gains: List[float] = []

    for row in rows:
        final_score = float(row.get("final_score", 0.0))
        verbose = str(row.get("response_verbose", "") or "")
        compressed = str(row.get("response_compressed", "") or "")

        # Check validity
        if not verbose or not compressed or final_score < min_score:
            invalid += 1
        else:
            v_len = max(len(verbose), 1)
            c_len = len(compressed)
            ratio = c_len / v_len
            compression_ratios.append(ratio)
            
            # Score gain relative to baseline
            gain = max(0.0, min(1.0, (final_score - 0.90) / 0.10))
            score_gains.append(gain)

    n = len(rows)
    contamination_rate = invalid / n if n > 0 else 1.0

    compression_density = (
        sum(compression_ratios) / len(compression_ratios)
        if compression_ratios
        else 0.0
    )
    
    fractal_score_gain = (
        sum(score_gains) / len(score_gains)
        if score_gains
        else 0.0
    )

    # TODO: Replace with real ontological drift variance from Tribunal
    drift_variance = 0.10

    return RewardComponents(
        contamination_rate=contamination_rate,
        compression_density=compression_density,
        fractal_score_gain=fractal_score_gain,
        drift_variance=drift_variance,
    )


def compute_curvature_stats(path: Path) -> tuple[int, int]:
    """
    Compute Euclidean vs Curved sample counts.

    Returns:
        Tuple of (euclidean_count, curved_count)
    """
    rows = _safe_json_lines(path)
    euclidean = 0
    curved = 0

    for row in rows:
        source = str(row.get("source", "")).upper()
        if "EUCLIDEAN" in source:
            euclidean += 1
        elif "CURVED" in source or "FUSION" in source:
            curved += 1

    return euclidean, curved


def log_iteration_metrics(metrics: IterationMetrics) -> None:
    """Append iteration metrics to Ouroboros log."""
    with OUROBOROS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")
        f.flush()


def adjust_config(
    config: OuroborosConfig,
    prev_reward: Optional[float],
    curr_reward: float,
    components: RewardComponents,
) -> OuroborosConfig:
    """
    PID-lite controller for auto-tuning parameters.

    Strategy:
    - If reward decreases: cool down temperature, reduce curvature (more Euclidean)
    - If reward increases: allow more temperature, increase curvature
    - If contamination high: aggressive cooldown
    - If compression low: increase temperature slightly

    Args:
        config: Current configuration
        prev_reward: Previous iteration reward (None for first iteration)
        curr_reward: Current iteration reward
        components: Current reward components

    Returns:
        Adjusted configuration for next iteration
    """
    new = OuroborosConfig(**asdict(config))

    if prev_reward is None:
        # First iteration, no adjustment
        return new

    reward_delta = curr_reward - prev_reward

    # Base adjustments based on reward trend
    if reward_delta < -0.05:
        # Significant degradation: cool down aggressively
        new.initial_temp = max(config.min_temp, config.initial_temp - 0.03)
        new.curvature_ratio = max(config.min_curvature_ratio, config.curvature_ratio - 0.08)
    elif reward_delta < 0:
        # Minor degradation: gentle cooldown
        new.initial_temp = max(config.min_temp, config.initial_temp - 0.02)
        new.curvature_ratio = max(config.min_curvature_ratio, config.curvature_ratio - 0.05)
    elif reward_delta > 0.05:
        # Significant improvement: allow more exploration
        new.initial_temp = min(config.max_temp, config.initial_temp + 0.02)
        new.curvature_ratio = min(config.max_curvature_ratio, config.curvature_ratio + 0.05)
    else:
        # Minor improvement: gentle increase
        new.initial_temp = min(config.max_temp, config.initial_temp + 0.01)
        new.curvature_ratio = min(config.max_curvature_ratio, config.curvature_ratio + 0.02)

    # Component-specific adjustments
    if components.contamination_rate > 0.15:
        # High contamination: force cooldown
        new.initial_temp = max(config.min_temp, new.initial_temp - 0.02)
        
    if components.compression_density < 0.4:
        # Poor compression: increase temperature slightly
        new.initial_temp = min(config.max_temp, new.initial_temp + 0.01)

    return new


def run_ouroboros(config: OuroborosConfig, verbose: bool = True) -> None:
    """
    Execute the Ouroboros feedback loop.

    Args:
        config: Ouroboros configuration
        verbose: Enable detailed logging
    """
    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"🐍 OUROBOROS PROTOCOL - FEEDBACK GOD-LOOP")
    print(f"{'='*70}")
    print(f"Domain: {config.domain}")
    print(f"Iterations: {config.max_iterations}")
    print(f"Batch Size: {config.batch_size}")
    print(f"Target Reward: {config.target_reward}")
    print(f"Log: {OUROBOROS_LOG}")
    print(f"{'='*70}\n")

    prev_reward: Optional[float] = None

    for iteration in range(1, config.max_iterations + 1):
        harvest_path = HARVEST_DIR / f"ouroboros_iter_{iteration:03d}.jsonl"

        print(f"\n{'─'*70}")
        print(f"🌀 Iteration {iteration}/{config.max_iterations}")
        print(f"{'─'*70}")
        print(f"Temperature:     {config.initial_temp:.3f}")
        print(f"Curvature Ratio: {config.curvature_ratio:.3f}")
        print(f"Output:          {harvest_path.name}")
        print(f"{'─'*70}\n")

        # Generate harvest
        try:
            run_curved_curriculum(
                count=config.batch_size,
                output_path=str(harvest_path),
                domain=config.domain,
                curved_ratio=config.curvature_ratio,
                verbose=verbose,
                max_rounds=5,
                target_score=0.99,
                min_acceptable_score=config.min_acceptable_score,
            )
        except Exception as e:
            print(f"❌ Harvest generation failed: {e}")
            continue

        # Compute metrics
        components = compute_metrics_from_harvest(harvest_path, config.min_acceptable_score)
        reward = compute_reward(components, RewardWeights())
        euclidean_count, curved_count = compute_curvature_stats(harvest_path)
        
        rows = _safe_json_lines(harvest_path)
        num_samples = len(rows)

        # Display metrics
        print(f"\n📊 Metrics:")
        print(f"   Samples:             {num_samples}")
        print(f"   Euclidean:           {euclidean_count}")
        print(f"   Curved:              {curved_count}")
        print(f"   Contamination:       {components.contamination_rate:.3f}")
        print(f"   Compression Density: {components.compression_density:.3f}")
        print(f"   Fractal Score Gain:  {components.fractal_score_gain:.3f}")
        print(f"   Drift Variance:      {components.drift_variance:.3f}")
        print(f"   🎯 Composite Reward: {reward:.3f}")

        if prev_reward is not None:
            delta = reward - prev_reward
            trend = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
            print(f"   {trend} Delta:           {delta:+.3f}")

        # Log metrics
        metrics = IterationMetrics(
            iteration=iteration,
            harvest_path=str(harvest_path),
            contamination_rate=components.contamination_rate,
            compression_density=components.compression_density,
            fractal_score_gain=components.fractal_score_gain,
            drift_variance=components.drift_variance,
            reward=reward,
            temperature=config.initial_temp,
            curvature_ratio=config.curvature_ratio,
            num_samples=num_samples,
            euclidean_count=euclidean_count,
            curved_count=curved_count,
        )
        log_iteration_metrics(metrics)

        # Check for early stopping
        if reward >= config.target_reward:
            print(f"\n✅ Target reward {config.target_reward} reached! Stopping early.")
            break

        # Adjust configuration for next iteration
        config = adjust_config(config, prev_reward, reward, components)
        prev_reward = reward

    print(f"\n{'='*70}")
    print(f"🎉 OUROBOROS COMPLETE")
    print(f"{'='*70}")
    print(f"Log: {OUROBOROS_LOG.absolute()}")
    print(f"Harvests: {HARVEST_DIR.absolute()}")
    print(f"{'='*70}\n")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Ouroboros Runner - Autonomous Feedback Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--domain",
        type=str,
        default="temporal_logic",
        help="Domain for paradox generation (default: temporal_logic)",
    )

    parser.add_argument(
        "--temp",
        type=float,
        default=1.10,
        help="Initial temperature (default: 1.10)",
    )

    parser.add_argument(
        "--curvature",
        type=float,
        default=0.50,
        help="Initial curvature ratio (default: 0.50)",
    )

    parser.add_argument(
        "--batch",
        type=int,
        default=20,
        help="Batch size per iteration (default: 20)",
    )

    parser.add_argument(
        "--iters",
        type=int,
        default=5,
        help="Maximum iterations (default: 5)",
    )

    parser.add_argument(
        "--target-reward",
        type=float,
        default=0.85,
        help="Target reward for early stopping (default: 0.85)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable verbose output",
    )

    args = parser.parse_args()

    config = OuroborosConfig(
        domain=args.domain,
        initial_temp=args.temp,
        curvature_ratio=args.curvature,
        batch_size=args.batch,
        max_iterations=args.iters,
        target_reward=args.target_reward,
    )
    
    run_ouroboros(config, verbose=not args.quiet)


if __name__ == "__main__":
    main()

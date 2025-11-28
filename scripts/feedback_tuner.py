#!/usr/bin/env python3
"""
Feedback Tuner - Adaptive Configuration Adjustment

Reads metrics from audit_log.json and adjusts generation parameters
for the next Ouroboros iteration based on contamination levels and scores.

Adjustment Strategy:
- High contamination (level 2 > 10%) → Decrease temp and curvature ratio
- Low drift + high scores → Increase temp and curvature ratio
- Updates experiment_log.jsonl with new config
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
EXPERIMENTS_DIR = DATA_DIR / "experiments"
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = EXPERIMENTS_DIR / "experiment_log.jsonl"
AUDIT_FILE = DATA_DIR / "audit_log.json"

# Tuning bounds
MIN_TEMP = 0.9
MAX_TEMP = 1.3
MIN_RATIO = 0.05
MAX_RATIO = 0.8

# Thresholds
HIGH_CONTAMINATION_THRESHOLD = 0.1  # 10% bad samples
LOW_DRIFT_THRESHOLD = 0.4
HIGH_SCORE_THRESHOLD = 0.94


# ═══════════════════════════════════════════════════════════════════════════
# FEEDBACK TUNER
# ═══════════════════════════════════════════════════════════════════════════


def load_audit_metrics() -> Optional[Dict[str, Any]]:
    """
    Load metrics from audit_log.json.
    
    Returns:
        Dict with audit metrics, or None if not found
    """
    if not AUDIT_FILE.exists():
        print(f"⚠️  Audit log not found: {AUDIT_FILE}")
        return None
    
    try:
        with AUDIT_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading audit log: {e}")
        return None


def load_last_config() -> Dict[str, Any]:
    """
    Load configuration from last experiment log entry.
    
    Returns:
        Dict with last config, or default values if not found
    """
    default_config = {
        "count": 10,
        "domain": "temporal_logic",
        "curved_ratio": 0.5,
        "temperature": 1.1,
        "max_rounds": 5,
        "target_score": 0.99,
        "min_score": 0.95,
    }
    
    if not LOG_FILE.exists():
        return default_config
    
    try:
        with LOG_FILE.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return default_config
            
            last_entry = json.loads(lines[-1])
            return last_entry.get("config_at_run", default_config)
    
    except Exception as e:
        print(f"⚠️  Error loading last config: {e}")
        return default_config


def compute_new_config(audit: Dict[str, Any], old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute new configuration based on audit metrics.
    
    Args:
        audit: Audit metrics from verify_harvest
        old_config: Previous configuration
        
    Returns:
        New configuration dict with adjusted parameters
    """
    new_config = old_config.copy()
    
    # Extract key metrics with safe defaults
    contamination_counts = audit.get("contamination_counts", {0: 0, 1: 0, 2: 0})
    total = audit.get("total_samples", 1)
    avg_score = audit.get("avg_final_score", 0.0)
    avg_drift = audit.get("avg_drift_score", 0.0)
    
    # Calculate contamination fraction
    bad_count = contamination_counts.get(2, 0) + contamination_counts.get("2", 0)
    bad_fraction = bad_count / max(total, 1)
    
    current_temp = old_config.get("temperature", 1.1)
    current_ratio = old_config.get("curved_ratio", 0.5)
    
    print(f"\n📊 Metrics Analysis:")
    print(f"   Avg Score: {avg_score:.3f}")
    print(f"   Avg Drift: {avg_drift:.3f}")
    print(f"   Bad Contamination: {bad_fraction:.1%}")
    print(f"   Current Temp: {current_temp:.3f}")
    print(f"   Current Ratio: {current_ratio:.3f}")
    
    # Decision logic
    adjustments = []
    
    if bad_fraction > HIGH_CONTAMINATION_THRESHOLD:
        # Too much contamination → be more conservative
        new_temp = max(MIN_TEMP, current_temp - 0.02)
        new_ratio = max(MIN_RATIO, current_ratio - 0.05)
        adjustments.append("⬇️  High contamination → decrease temp and ratio")
    
    elif avg_drift < LOW_DRIFT_THRESHOLD and avg_score > HIGH_SCORE_THRESHOLD:
        # Low drift + high scores → we can be more aggressive
        new_temp = min(MAX_TEMP, current_temp + 0.01)
        new_ratio = min(MAX_RATIO, current_ratio + 0.02)
        adjustments.append("⬆️  Low drift + high scores → increase temp and ratio")
    
    else:
        # No major adjustment needed
        new_temp = current_temp
        new_ratio = current_ratio
        adjustments.append("✅ Metrics within acceptable range → no adjustment")
    
    new_config["temperature"] = new_temp
    new_config["curved_ratio"] = new_ratio
    
    print(f"\n🔧 Adjustments:")
    for adj in adjustments:
        print(f"   {adj}")
    print(f"   New Temp: {new_temp:.3f} (Δ {new_temp - current_temp:+.3f})")
    print(f"   New Ratio: {new_ratio:.3f} (Δ {new_ratio - current_ratio:+.3f})")
    
    return new_config


def append_tuning_entry(old_config: Dict[str, Any], new_config: Dict[str, Any], audit: Dict[str, Any]) -> None:
    """
    Append feedback tuning entry to experiment log.
    
    Args:
        old_config: Previous configuration
        new_config: New configuration after tuning
        audit: Audit metrics that drove the decision
    """
    entry = {
        "event": "feedback_tuning",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "old_config": old_config,
        "new_config": new_config,
        "metrics_snapshot": audit,
    }
    
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Feedback entry appended to {LOG_FILE}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Apply feedback tuning based on audit metrics."""
    parser = argparse.ArgumentParser(
        description="Feedback Tuner - Adaptive configuration adjustment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run feedback tuning (uses default paths)
  python scripts/feedback_tuner.py

  # Specify custom log path
  python scripts/feedback_tuner.py --log-path data/custom_log.jsonl

The tuner:
- Reads audit_log.json for metrics
- Loads last config from experiment_log.jsonl
- Computes adjusted config based on contamination and drift
- Appends tuning entry to experiment log
        """
    )
    
    parser.add_argument(
        "--log-path",
        type=str,
        default=None,
        help=f"Path to experiment log (default: {LOG_FILE})",
    )
    
    args = parser.parse_args()
    
    # Override log path if specified
    if args.log_path:
        global LOG_FILE
        LOG_FILE = Path(args.log_path)
    
    print(f"\n{'='*70}")
    print(f"🔧 FEEDBACK TUNER")
    print(f"{'='*70}\n")
    
    # Load audit metrics
    audit = load_audit_metrics()
    if not audit:
        print("❌ No audit metrics available. Cannot tune.")
        sys.exit(1)
    
    # Load last config
    old_config = load_last_config()
    
    # Compute new config
    new_config = compute_new_config(audit, old_config)
    
    # Append entry
    append_tuning_entry(old_config, new_config, audit)
    
    print(f"\n{'='*70}")
    print(f"🎉 FEEDBACK TUNING COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

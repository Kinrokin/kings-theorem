#!/usr/bin/env python3
"""
Ouroboros Supervisor - Hybrid Pipeline Orchestration

Supervises one full autonomous cycle:
1. Generate synthetic data batch (local)
2. Verify + purify (local)
3. Apply feedback tuning (local)
4. Prepare Colab job descriptor (no auto-run)
5. Append experiment log entry

The supervisor maintains iteration state and config in experiment_log.jsonl.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PURIFIED_DIR = DATA_DIR / "purified"
EXPERIMENTS_DIR = DATA_DIR / "experiments"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
PURIFIED_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = EXPERIMENTS_DIR / "experiment_log.jsonl"

# Default configuration for first iteration
DEFAULT_CONFIG = {
    "count": 10,
    "domain": "temporal_logic",
    "curved_ratio": 0.5,
    "temperature": 1.1,
    "max_rounds": 5,
    "target_score": 0.99,
    "min_score": 0.95,
}


# ═══════════════════════════════════════════════════════════════════════════
# SUPERVISOR CLASS
# ═══════════════════════════════════════════════════════════════════════════


class OuroborosSupervisor:
    """
    Orchestrates the full Ouroboros cycle.
    
    Manages iteration state, executes pipeline phases, and maintains logs.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize supervisor.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.iteration = 1
        self.config = DEFAULT_CONFIG.copy()
        
        # Load last config if exists
        self._load_last_config()
    
    def _load_last_config(self) -> None:
        """
        Load configuration from last experiment log entry.
        
        If log exists, reads the last entry and increments iteration.
        Otherwise uses DEFAULT_CONFIG.
        """
        if not LOG_FILE.exists():
            if self.verbose:
                print(f"📋 No experiment log found. Starting fresh at iteration {self.iteration}")
            return
        
        try:
            with LOG_FILE.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return
                
                # Parse last entry
                last_entry = json.loads(lines[-1])
                
                # Increment iteration
                self.iteration = last_entry.get("iteration", 0) + 1
                
                # Load config if available
                if "config_at_run" in last_entry:
                    self.config.update(last_entry["config_at_run"])
                
                if self.verbose:
                    print(f"📋 Loaded config from last run. Starting iteration {self.iteration}")
        
        except Exception as e:
            print(f"⚠️  Error loading experiment log: {e}")
            print("   Using default config")
    
    def _execute_phase(self, cmd: List[str], name: str) -> bool:
        """
        Execute a pipeline phase via subprocess.
        
        Args:
            cmd: Command to execute (list of strings)
            name: Human-readable phase name for logging
            
        Returns:
            True if phase succeeded, False otherwise
        """
        if self.verbose:
            print(f"\n{'='*70}")
            print(f"▶️  Phase: {name}")
            print(f"   Command: {' '.join(cmd)}")
            print(f"{'='*70}")
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            
            if self.verbose and result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print(f"⚠️  stderr:\n{result.stderr}")
            
            if self.verbose:
                print(f"✅ Phase '{name}' completed successfully\n")
            
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Phase '{name}' failed with exit code {e.returncode}")
            if e.stdout:
                print(f"stdout:\n{e.stdout}")
            if e.stderr:
                print(f"stderr:\n{e.stderr}")
            return False
        
        except Exception as e:
            print(f"❌ Phase '{name}' failed with exception: {e}")
            return False
    
    def run_cycle(self) -> bool:
        """
        Execute one complete Ouroboros cycle.
        
        Phases:
        1. Generate batch
        2. Verify + purify
        3. Apply feedback
        4. Prepare Colab job
        5. Log results
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        start_time = datetime.now(timezone.utc)
        
        print(f"\n{'='*70}")
        print(f"🐍 OUROBOROS CYCLE - ITERATION {self.iteration}")
        print(f"{'='*70}")
        print(f"Config: {json.dumps(self.config, indent=2)}")
        print(f"Start time: {start_time.isoformat()}")
        print(f"{'='*70}\n")
        
        # Define output paths for this iteration
        raw_path = RAW_DIR / f"harvest_iter_{self.iteration:03d}.jsonl"
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 1: Generate batch
        # ═══════════════════════════════════════════════════════════════════
        
        gen_cmd = [
            sys.executable,  # Use current Python interpreter
            str(REPO_ROOT / "scripts" / "run_curved_curriculum.py"),
            "--count", str(self.config["count"]),
            "--output", str(raw_path),
            "--domain", self.config["domain"],
            "--curved-ratio", str(self.config["curved_ratio"]),
            "--max-rounds", str(self.config["max_rounds"]),
            "--target-score", str(self.config["target_score"]),
            "--min-score", str(self.config["min_score"]),
        ]
        
        if not self.verbose:
            gen_cmd.append("--quiet")
        
        if not self._execute_phase(gen_cmd, "Generation"):
            return False
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 2: Verify + purify
        # ═══════════════════════════════════════════════════════════════════
        
        verify_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "verify_harvest.py"),
            "--input", str(raw_path),
        ]
        
        if not self.verbose:
            verify_cmd.append("--quiet")
        
        if not self._execute_phase(verify_cmd, "Verification"):
            return False
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 3: Apply feedback tuning
        # ═══════════════════════════════════════════════════════════════════
        
        feedback_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "feedback_tuner.py"),
        ]
        
        if not self._execute_phase(feedback_cmd, "Feedback Tuning"):
            print("⚠️  Feedback tuning failed but continuing...")
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 4: Prepare Colab job descriptor
        # ═══════════════════════════════════════════════════════════════════
        
        cloud_cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "cloud_tuner.py"),
            "prepare-job",
            "--purified", str(PURIFIED_DIR / "purified_harvest.jsonl"),
        ]
        
        if not self._execute_phase(cloud_cmd, "Cloud Job Preparation"):
            print("⚠️  Cloud job prep failed but continuing...")
        
        # ═══════════════════════════════════════════════════════════════════
        # Phase 5: Append log entry
        # ═══════════════════════════════════════════════════════════════════
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Read audit metrics if available
        audit_path = DATA_DIR / "audit_log.json"
        audit_metrics = {}
        if audit_path.exists():
            try:
                with audit_path.open("r", encoding="utf-8") as f:
                    audit_metrics = json.load(f)
            except Exception as e:
                print(f"⚠️  Could not read audit log: {e}")
        
        log_entry = {
            "iteration": self.iteration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "config_at_run": self.config.copy(),
            "raw_path": str(raw_path),
            "purified_path": str(PURIFIED_DIR / "purified_harvest.jsonl"),
            "audit_path": str(audit_path),
            "metrics": audit_metrics,
        }
        
        # Append to log
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        print(f"\n{'='*70}")
        print(f"🎉 OUROBOROS CYCLE {self.iteration} COMPLETE")
        print(f"{'='*70}")
        print(f"Duration: {duration:.1f}s")
        print(f"Raw output: {raw_path}")
        print(f"Purified output: {PURIFIED_DIR / 'purified_harvest.jsonl'}")
        print(f"Log updated: {LOG_FILE}")
        print(f"{'='*70}\n")
        
        return True


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Run one Ouroboros cycle."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ouroboros Supervisor - Run one complete autonomous cycle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run one cycle (verbose)
  python scripts/run_ouroboros.py

  # Run quietly
  python scripts/run_ouroboros.py --quiet

The supervisor automatically:
- Loads config from last experiment log entry
- Increments iteration number
- Runs generation → verification → feedback → cloud prep
- Logs all results to data/experiments/experiment_log.jsonl
        """
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    
    args = parser.parse_args()
    
    supervisor = OuroborosSupervisor(verbose=not args.quiet)
    success = supervisor.run_cycle()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

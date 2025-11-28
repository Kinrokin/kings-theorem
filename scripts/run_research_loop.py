"""
AID: /scripts/run_research_loop.py
Proof ID: PRF-LOOP-H-PRIME-001
Axiom: Axiom 1 (Anti-Fragility), Axiom 3 (Auditability)
Purpose: Industrial-grade autonomous research loop orchestrator.

H-PRIME Protocol Implementation:
- Lazarus Repair: Automatic crash recovery with bounded retry budget
- Cryptographic Ledger: Immutable audit trail for all operations
- Risk Budget Enforcement: Maximum crashes before human escalation
- Dry-Run Mode: CI-safe execution without GPU/API calls
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# Adjust path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from src.primitives.dual_ledger import DualLedger as _DualLedger

    DualLedger = _DualLedger  # type: ignore
except ImportError:
    # Fallback ledger implementation
    class DualLedger:  # type: ignore
        def __init__(self) -> None:
            self.chain: list[Dict[str, Any]] = []

        def log(self, role: str, action: str, data: str) -> None:
            self.chain.append({"role": role, "action": action, "data": data, "ts": time.time()})


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Generators
try:
    from src.crucibles.level7_generator import Level7ParadoxGenerator
except Exception:
    Level7ParadoxGenerator = None  # type: ignore


@dataclass
class LoopState:
    """Immutable snapshot of research loop state."""

    level: int
    epoch: int
    best_metric: float
    safety_violations: int
    crash_counter: int
    last_update_ts: float
    notes: str = ""


class ResearchLoop:
    """
    Master orchestrator for autonomous curriculum learning.

    Implements the H-PRIME protocol:
    1. Generate Crucibles (adversarial test cases)
    2. Refine & Filter (quality assurance)
    3. Train (SFT with Unsloth)
    4. Evaluate (safety & capability checks)
    5. Promote or Rollback (curriculum advancement)
    """

    def __init__(
        self,
        data_dir: Path,
        models_dir: Path,
        dry_run: bool = False,
        max_crashes: int = 10,
    ) -> None:
        self.data_dir = data_dir
        self.models_dir = models_dir
        self.dry_run = dry_run
        self.max_crashes = max_crashes

        self.state_file = data_dir / "system_state.json"
        self.ledger = DualLedger()

        # Human oversight controls
        self.ready_to_promote = False
        self.previous_accuracy = 0.0
        self.sanity_improvement_threshold = 0.3  # Flag if accuracy jumps > 30% in one epoch

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[INIT] ResearchLoop initialized (dry_run={dry_run})")
        self.ledger.log("System", "INIT", f"Loop started in {'DRY_RUN' if dry_run else 'LIVE'} mode")

    def load_state(self) -> LoopState:
        """Load loop state from disk or initialize."""
        if not self.state_file.exists():
            logger.info("State file not found, initializing fresh state")
            return LoopState(
                level=1,
                epoch=0,
                best_metric=0.0,
                safety_violations=0,
                crash_counter=0,
                last_update_ts=time.time(),
                notes="Initial state",
            )

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return LoopState(**raw)
        except Exception as e:
            logger.exception(f"Failed to load state, reinitializing: {e}")
            return LoopState(
                level=1,
                epoch=0,
                best_metric=0.0,
                safety_violations=0,
                crash_counter=0,
                last_update_ts=time.time(),
                notes=f"Reinitialized after error: {e}",
            )

    def save_state(self, state: LoopState) -> None:
        """Persist state to disk with cryptographic seal."""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(asdict(state), f, indent=2)

            # Log to immutable ledger
            self.ledger.log(
                "System", "STATE_SAVE", f"Epoch {state.epoch}, Level {state.level}, Metric {state.best_metric:.3f}"
            )
            logger.info(f"✅ State saved: epoch={state.epoch}, level={state.level}")
        except Exception as e:
            logger.exception(f"Failed to save state: {e}")

    def _check_human_intervention(self, state: LoopState) -> None:
        """
        Check for local signal files to pause, stop, or gate level promotions.

        Signal Files:
        - data/STOP: Gracefully save state and exit
        - data/PAUSE: Freeze loop until file is removed
        - data/ALLOW_LEVEL_X: Required to promote to level X
        """
        # 1. STOP SIGNAL
        stop_file = self.data_dir / "STOP"
        if stop_file.exists():
            logger.warning("🛑 STOP signal detected. Saving state and exiting...")
            self.save_state(state)
            self.ledger.log("System", "STOP", "Human-initiated graceful shutdown")
            sys.exit(0)

        # 2. PAUSE SIGNAL
        pause_file = self.data_dir / "PAUSE"
        while pause_file.exists():
            logger.warning("⏸️ PAUSE signal detected. Loop frozen. Delete 'data/PAUSE' to resume.")
            time.sleep(10)
            # Check for STOP during pause
            if stop_file.exists():
                self._check_human_intervention(state)

        # 3. LEVEL UP GATE (Prevent unauthorized capability jumps)
        if self.ready_to_promote:
            next_level = state.level + 1
            lock_file = self.data_dir / f"ALLOW_LEVEL_{next_level}"

            if not lock_file.exists():
                logger.warning(f"🔒 Promotion to Level {next_level} is LOCKED. Waiting for human approval...")
                logger.info(f"👉 To approve, run: touch data/ALLOW_LEVEL_{next_level}")
                self.ledger.log("System", "PROMOTION_BLOCKED", f"Level {next_level} requires approval")

                # Wait for human approval
                while not lock_file.exists():
                    time.sleep(10)
                    # Check for STOP/PAUSE during wait
                    if stop_file.exists():
                        self._check_human_intervention(state)
                    if pause_file.exists():
                        logger.info("⏸️ Paused while waiting for level approval")
                        while pause_file.exists():
                            time.sleep(10)
                            if stop_file.exists():
                                self._check_human_intervention(state)

                logger.info(f"✅ Level {next_level} approval granted by human operator")
                self.ledger.log("System", "PROMOTION_APPROVED", f"Level {next_level} unlocked")
                # Remove the lock file after use
                lock_file.unlink()

    def _sanity_check(self, old_metric: float, new_metric: float, state: LoopState) -> None:
        """
        Circuit breaker for anomalous performance changes.

        Flags:
        - Improvement too fast (> 30% in one epoch) - possible data leakage
        - Performance drop too sharp (> 20% decline) - possible model degradation
        """
        improvement = new_metric - old_metric

        # Check for suspiciously fast improvement
        if improvement > self.sanity_improvement_threshold:
            logger.critical(f"🚨 SANITY CHECK FAILED: Accuracy jumped {improvement:.1%} in one epoch!")
            logger.critical("   This may indicate data leakage or evaluation corruption.")
            self.ledger.log("System", "SANITY_FAIL", f"Suspicious improvement: {improvement:.3f}")

            # Create PAUSE file automatically
            pause_file = self.data_dir / "PAUSE"
            pause_file.touch()
            logger.warning("   Auto-pausing loop for human inspection. Check logs and data.")
            self._check_human_intervention(state)

        # Check for catastrophic performance drop
        if improvement < -0.2:  # 20% drop
            logger.error(f"⚠️ PERFORMANCE DEGRADATION: Accuracy dropped {abs(improvement):.1%}")
            logger.error("   Model may have been corrupted or training destabilized.")
            self.ledger.log("System", "DEGRADATION", f"Performance drop: {improvement:.3f}")

            # Create PAUSE file automatically
            pause_file = self.data_dir / "PAUSE"
            pause_file.touch()
            logger.warning("   Auto-pausing loop for human inspection.")
            self._check_human_intervention(state)

    # Compatibility alias for sentinel tests and external callers
    def _check_signals(self, state: LoopState) -> None:
        """Alias to `_check_human_intervention` for Dead Man's Switch checks."""
        self._check_human_intervention(state)

    def step_1_generate(self, level: int) -> Path:
        """
        Generate Crucibles (adversarial test cases).

        Returns:
            Path to generated crucibles file.
        """
        logger.info(f"[STEP 1] Generating Crucibles for Level {level}")
        output_file = self.data_dir / f"raw_crucibles_L{level}.jsonl"

        # Level-aware generation strategy
        if level >= 7 and Level7ParadoxGenerator is not None:
            logger.info("[GEN] Using Level7ParadoxGenerator for D7 paradoxes")
            # In dry-run, still emit a realistic-looking entry
            if self.dry_run:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "id": "L7-mock",
                                "difficulty": 7,
                                "domains": ["Corporate Law", "Ethics Committee"],
                                "paradox_type": "temporal_regulatory_conflict",
                            }
                        )
                        + "\n"
                    )
                return output_file

            # Live generation via Python API
            generator = Level7ParadoxGenerator()
            crucibles = generator.generate_batch(10)
            with open(output_file, "w", encoding="utf-8") as f:
                for c in crucibles:
                    f.write(json.dumps(c.to_dict()) + "\n")
            logger.info(f"✅ Generated L7 crucibles: {output_file}")
            return output_file

        # Legacy path for Levels 1-6
        if self.dry_run:
            logger.info("[DRY RUN] Skipping actual generation, creating mock file")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json.dumps({"id": "mock_crucible", "difficulty": level}) + "\n")
            return output_file

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/generate_crucibles.py",
                    "--level",
                    str(level),
                    "--output",
                    str(output_file),
                    "--count",
                    "1000",
                ],
                capture_output=True,
                text=True,
                timeout=600,
                check=True,
            )
            logger.info(f"✅ Generated crucibles: {output_file}")
            logger.debug(f"Generator output: {result.stdout[:500]}")
            return output_file

        except subprocess.TimeoutExpired:
            logger.error("Crucible generation timed out")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Crucible generation failed: {e.stderr}")
            raise

    def step_2_refine(self, input_file: Path) -> Path:
        """
        Refine and filter crucibles for quality.

        Returns:
            Path to SFT-ready dataset.
        """
        logger.info("[STEP 2] Refining Crucibles")
        output_file = self.data_dir / "sft_ready.jsonl"

        if self.dry_run:
            logger.info("[DRY RUN] Copying input to output")
            import shutil

            shutil.copy(input_file, output_file)
            return output_file

        try:
            _ = subprocess.run(
                [
                    sys.executable,
                    "scripts/refine_dataset.py",
                    "--input",
                    str(input_file),
                    "--output",
                    str(output_file),
                    "--min-quality",
                    "0.7",
                ],
                capture_output=True,
                text=True,
                timeout=300,
                check=True,
            )
            logger.info(f"✅ Refined dataset: {output_file}")
            return output_file

        except Exception as e:
            logger.exception(f"Refinement failed: {e}")
            raise

    def step_3_train(self, dataset_file: Path, epoch: int) -> Path:
        """
        Run SFT training with Unsloth.

        Returns:
            Path to trained model checkpoint.
        """
        logger.info(f"[STEP 3] Training Epoch {epoch}")
        checkpoint_dir = self.models_dir / f"checkpoint_epoch_{epoch}"

        if self.dry_run:
            logger.info("[DRY RUN] Skipping training, creating mock checkpoint")
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            (checkpoint_dir / "config.json").write_text("{}")
            return checkpoint_dir

        try:
            _ = subprocess.run(
                [
                    sys.executable,
                    "scripts/train_unsloth.py",
                    "--dataset",
                    str(dataset_file),
                    "--output",
                    str(checkpoint_dir),
                    "--epochs",
                    "3",
                    "--lr",
                    "2e-4",
                ],
                capture_output=True,
                text=True,
                timeout=7200,
                check=True,
            )
            logger.info(f"✅ Training complete: {checkpoint_dir}")
            return checkpoint_dir

        except subprocess.TimeoutExpired:
            logger.error("Training timed out")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Training failed: {e.stderr}")
            raise

    def step_4_eval(self, checkpoint_dir: Path) -> Dict[str, Any]:
        """
        Evaluate model safety and capability.

        Returns:
            Evaluation metrics dict.
        """
        logger.info("[STEP 4] Evaluating Model")

        if self.dry_run:
            logger.info("[DRY RUN] Returning mock eval results")
            return {"accuracy": 0.85, "safety_score": 0.92, "passed": True}

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/eval_safety.py",
                    "--checkpoint",
                    str(checkpoint_dir),
                    "--test-set",
                    str(self.data_dir / "eval_set.jsonl"),
                ],
                capture_output=True,
                text=True,
                timeout=600,
                check=True,
            )

            metrics = json.loads(result.stdout)
            logger.info(f"✅ Evaluation results: {metrics}")
            return metrics

        except Exception as e:
            logger.exception(f"Evaluation failed: {e}")
            return {"accuracy": 0.0, "safety_score": 0.0, "passed": False}

    def step_5_decide(self, state: LoopState, eval_metrics: Dict[str, Any]) -> LoopState:
        """
        Decide whether to promote, rollback, or continue.

        Returns:
            Updated state.
        """
        logger.info("[STEP 5] Making Curriculum Decision")

        accuracy = eval_metrics.get("accuracy", 0.0)
        safety_score = eval_metrics.get("safety_score", 0.0)

        # Safety threshold enforcement (Axiom 6: Ethics >= 0.7)
        if safety_score < 0.7:
            logger.warning(f"⚠️ Safety violation detected: {safety_score:.3f}")
            return LoopState(
                level=state.level,
                epoch=state.epoch + 1,
                best_metric=state.best_metric,
                safety_violations=state.safety_violations + 1,
                crash_counter=state.crash_counter,
                last_update_ts=time.time(),
                notes=f"Safety violation: {safety_score:.3f} < 0.7",
            )

        # Promotion logic with human gate
        if accuracy > state.best_metric:
            logger.info(f"📈 Metric improved: {state.best_metric:.3f} → {accuracy:.3f}")

            # Check if promotion threshold reached
            if accuracy > 0.9:
                self.ready_to_promote = True
                new_level = state.level + 1
                logger.info(f"🎓 Promotion threshold reached: Level {state.level} → {new_level}")
                logger.info("   Waiting for human approval at gate...")
            else:
                self.ready_to_promote = False
                new_level = state.level

            return LoopState(
                level=new_level,
                epoch=state.epoch + 1,
                best_metric=accuracy,
                safety_violations=state.safety_violations,
                crash_counter=state.crash_counter,
                last_update_ts=time.time(),
                notes=f"Promoted to Level {new_level}" if new_level > state.level else "Improved within level",
            )

        # No improvement
        logger.info(f"📊 No improvement: {accuracy:.3f} <= {state.best_metric:.3f}")
        return LoopState(
            level=state.level,
            epoch=state.epoch + 1,
            best_metric=state.best_metric,
            safety_violations=state.safety_violations,
            crash_counter=state.crash_counter,
            last_update_ts=time.time(),
            notes="Continuing current level",
        )

    def run_single_epoch(self, state: LoopState) -> LoopState:
        """
        Execute one complete training epoch with Lazarus repair.
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 EPOCH {state.epoch + 1} | LEVEL {state.level}")
        logger.info(f"{'='*60}\n")

        # Check for human intervention signals before starting epoch
        self._check_human_intervention(state)

        try:
            crucibles_file = self.step_1_generate(state.level)
            self.ledger.log("Loop", "GENERATE", f"Created {crucibles_file.name}")

            sft_file = self.step_2_refine(crucibles_file)
            self.ledger.log("Loop", "REFINE", f"Created {sft_file.name}")

            checkpoint = self.step_3_train(sft_file, state.epoch + 1)
            self.ledger.log("Loop", "TRAIN", f"Saved to {checkpoint.name}")

            metrics = self.step_4_eval(checkpoint)
            self.ledger.log("Loop", "EVAL", json.dumps(metrics))

            # Sanity check for anomalous performance changes
            new_accuracy = metrics.get("accuracy", 0.0)
            self._sanity_check(state.best_metric, new_accuracy, state)

            new_state = self.step_5_decide(state, metrics)

            # Check for level-up gate if promotion is pending
            if self.ready_to_promote:
                self._check_human_intervention(new_state)

            self.save_state(new_state)

            return new_state

        except KeyboardInterrupt:
            logger.warning("Received interrupt signal")
            raise
        except Exception as e:
            logger.exception(f"❌ Epoch failed: {e}")
            # Lazarus repair
            crashed_state = LoopState(
                level=state.level,
                epoch=state.epoch + 1,
                best_metric=state.best_metric,
                safety_violations=state.safety_violations,
                crash_counter=state.crash_counter + 1,
                last_update_ts=time.time(),
                notes=f"Crashed: {str(e)[:100]}",
            )
            self.save_state(crashed_state)
            return crashed_state

    def run(self, max_steps: Optional[int] = None) -> None:
        """
        Main loop runner.

        Args:
            max_steps: If set, runs for N epochs then exits.
        """
        logger.info("🚀 Starting Research Loop")

        state = self.load_state()
        steps_completed = 0

        try:
            while True:
                # Dead Man's Switch: check signals before any work
                self._check_human_intervention(state)
                if state.crash_counter >= self.max_crashes:
                    logger.critical(f"💀 Crash budget exhausted: {state.crash_counter}/{self.max_crashes}")
                    self.ledger.log("System", "HALT", "Maximum crashes reached")
                    break

                state = self.run_single_epoch(state)
                steps_completed += 1

                if max_steps and steps_completed >= max_steps:
                    logger.info(f"✅ Completed {steps_completed} steps")
                    break

                time.sleep(2)

        except KeyboardInterrupt:
            logger.info("\n🛑 Graceful shutdown initiated")
            self.ledger.log("System", "SHUTDOWN", "User interrupt")
        finally:
            logger.info(f"Final state: {state}")
            logger.info(f"Ledger entries: {len(self.ledger.chain)}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KT H-PRIME Research Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "models",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="CI-safe mode without GPU/API calls",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Maximum epochs (default: infinite)",
    )
    parser.add_argument(
        "--max-crashes",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    loop = ResearchLoop(
        data_dir=args.data_dir,
        models_dir=args.models_dir,
        dry_run=args.dry_run,
        max_crashes=args.max_crashes,
    )

    loop.run(max_steps=args.steps)


if __name__ == "__main__":
    main()

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, TypedDict


def run_step(cmd_list: list[str], description: str, cwd: str | None = None) -> str:
    """
    Run a shell command, log timing, and raise on failure.

    This is deliberately synchronous so you can watch each stage.
    """
    print(f"\n🚀 [STEP] {description}")
    print(f"   Command: {' '.join(cmd_list)}")
    start = time.time()
    result = subprocess.run(
        cmd_list,
        capture_output=True,
        text=True,
        cwd=cwd or ".",
    )
    duration = time.time() - start

    if result.returncode != 0:
        print(f"❌ FAILED in {duration:.1f}s")
        if result.stdout:
            print("STDOUT:\n", result.stdout)
        if result.stderr:
            print("STDERR:\n", result.stderr)
        raise RuntimeError(f"Step failed: {description}")

    print(f"✅ COMPLETED in {duration:.1f}s ({duration:.1f}s)")
    if result.stdout:
        print("   STDOUT (truncated):")
        print("   " + "\n   ".join(result.stdout.splitlines()[:10]))
    return result.stdout.strip()


def load_state(run_dir: Path) -> Dict[str, Any]:
    """
    Load loop state {level, epoch, best_metric}, or initialize if absent.
    """
    state_file = run_dir / "state.json"
    if not state_file.exists():
        return {"level": 1, "epoch": 0, "best_metric": 0.0}
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(run_dir: Path, state: Dict[str, Any]) -> None:
    state_file = run_dir / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def write_epoch_summary(
    epoch_dir: Path,
    level: int,
    epoch: int,
    metric: float | None,
    notes: str = "",
) -> None:
    class SummaryDict(TypedDict):
        level: int
        epoch: int
        metric: float | None
        notes: str
        path: str

    summary: SummaryDict = {
        "level": level,
        "epoch": epoch,
        "metric": metric,
        "notes": notes,
        "path": str(epoch_dir),
    }
    out_path = epoch_dir / "epoch_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

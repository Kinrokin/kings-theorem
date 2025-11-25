"""CI Bias/Emotion/Composition invariants enforcement.

Runs pytest markers and computes minimal diversity metrics.
Fails if:
 - Any marker suite fails.
 - Diversity traditions count < MIN_TRADITIONS across kt_bias tests.
 - Emotion drift dominance (simulated) exceeds threshold (placeholder integration point).
 - Composition theorem failures present (dsl_theorems with any False result if available).

This is intentionally lightweight; deeper semantic metrics can be added later.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_TRADITIONS = 1  # raise later


def run_marker(marker: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pytest", "-q", f"-m {marker}", "--disable-warnings"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def extract_traditions(text: str) -> int:
    traditions = {"christian", "islamic", "hindu", "secular", "buddhist", "jewish"}
    found = set()
    for line in text.lower().splitlines():
        for t in traditions:
            if t in line:
                found.add(t)
    return len(found)


def main():
    failures = []
    bias = run_marker("kt_bias")
    emotion = run_marker("kt_emotion")
    composition = run_marker("kt_composition")

    if bias.returncode != 0:
        failures.append("kt_bias tests failed")
    if emotion.returncode != 0:
        failures.append("kt_emotion tests failed")
    if composition.returncode != 0:
        failures.append("kt_composition tests failed")

    diversity = extract_traditions(bias.stdout + bias.stderr)
    if diversity < MIN_TRADITIONS:
        failures.append(f"Tradition diversity below minimum ({diversity} < {MIN_TRADITIONS})")

    # Placeholder: parse potential DSL theorem evaluation lines (if printed)
    theorems_failed = False
    for line in (composition.stdout + composition.stderr).splitlines():
        if line.strip().startswith("DSL_THEOREM_FAIL"):
            theorems_failed = True
            break
    if theorems_failed:
        failures.append("Composition DSL theorem failure detected")

    result = {
        "bias_returncode": bias.returncode,
        "emotion_returncode": emotion.returncode,
        "composition_returncode": composition.returncode,
        "diversity_traditions": diversity,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()

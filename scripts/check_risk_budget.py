"""CI check: run counterfactual risk and enforce risk_budget.yml bounds.

Exits non-zero if catastrophic probability exceeds budget or if insufficient samples.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.risk.budget import load_risk_budget  # noqa: E402
from src.risk.guard import run_counterfactuals  # noqa: E402


def main():
    budget = load_risk_budget(ROOT / "config" / "risk_budget.yml")
    if not budget:
        print("No risk budget configured; skipping.")
        sys.exit(0)
    risk = run_counterfactuals(samples=budget.min_samples)
    report = {
        "catastrophic_prob": risk.catastrophic_prob,
        "samples": risk.samples,
        "budget": {
            "catastrophic_max": budget.catastrophic_max,
            "min_samples": budget.min_samples,
        },
    }
    print(json.dumps(report, indent=2))
    if risk.samples < budget.min_samples or risk.catastrophic_prob > budget.catastrophic_max:
        print("Risk budget exceeded", file=sys.stderr)
        sys.exit(1)
    print("Risk budget OK")


if __name__ == "__main__":
    main()

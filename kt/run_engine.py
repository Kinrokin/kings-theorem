"""Phoenix Phase 4 Execution Harness

Provides a simple CLI invocation path: `python -m kt.run_engine`
Runs a sample problem through the unified KTEngine and prints a
compact summary surface for verification.
"""

import json
import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kt import KTEngine  # noqa: E402
from src.logging_config import setup_logging  # noqa: E402

setup_logging()
logger = logging.getLogger("kt.run")


def sample_problem() -> dict:
    return {
        "task": "Portfolio Ethics Rebalance",
        "data": {"positions": ["AAPL", "TSLA"], "exposure": 0.72},
        "constraint": "RISK < 15% AND MAXIMIZE PROFIT WITHOUT SACRIFICE_MINORITY",
        "proposed_actions": [{"type": "DANGEROUS_TRADE", "utility": 500}],  # triggers guardrail
    }


def main():
    logger.info("[RUN] Initializing KTEngine for sample execution")
    engine = KTEngine()
    problem = sample_problem()
    result = engine.execute(problem)
<<<<<<< Updated upstream
=======
    risk = result.get("risk", {})
>>>>>>> Stashed changes
    summary = {
        "status": result.get("status"),
        "decision": result.get("governance", {}).get("decision"),
        "trace_valid": result.get("trace_valid"),
        "lattice_ok": result.get("lattice_ok"),
        "rationale": result.get("rationale"),
<<<<<<< Updated upstream
=======
        "risk": {
            "tier": risk.get("tier", "LOW"),
            "aggregate": risk.get("aggregate", 0.0),
            "components": risk.get("components", {}),
        },
        "trace_preview": result.get("trace", [])[:5],
>>>>>>> Stashed changes
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

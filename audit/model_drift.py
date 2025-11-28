"""Phase 5 Model Drift Audit

Detects governance/risk regressions after model or config updates.

Workflow:
  1. Capture baseline risk profile for a suite of canonical scenarios
  2. Run same scenarios after model/config update
  3. Compare risk tier, aggregate, and governance decisions
  4. Fail audit if tier worsens or decisions regress without explicit approval

Prevents silent degradation in ethical/safety posture.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ModelDriftDetector:
    """Compares baseline vs. current risk profiles to detect governance regression."""

    def __init__(self, baseline_path: str | Path | None = None):
        self.baseline_path = Path(baseline_path) if baseline_path else Path("audit/baseline_risk.json")
        self.baseline: Dict[str, Dict[str, Any]] = {}
        if self.baseline_path.exists():
            self._load_baseline()

    def _load_baseline(self) -> None:
        with self.baseline_path.open("r", encoding="utf-8") as f:
            self.baseline = json.load(f)
        logger.info("[DRIFT] Loaded baseline with %d scenarios", len(self.baseline))

    def save_baseline(self, scenario_results: Dict[str, Dict[str, Any]]) -> None:
        """Persist current scenario results as new baseline."""

        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with self.baseline_path.open("w", encoding="utf-8") as f:
            json.dump(scenario_results, f, indent=2)
        self.baseline = scenario_results
        logger.info("[DRIFT] Saved baseline with %d scenarios", len(scenario_results))

    def detect_drift(
        self,
        current_results: Dict[str, Dict[str, Any]],
        max_aggregate_increase: float = 0.1,
    ) -> Dict[str, Any]:
        """Compare current results to baseline; flag regressions.

        Args:
            current_results: {scenario_id: {"risk": {...}, "governance": {...}}}
            max_aggregate_increase: tolerable increase in aggregate risk

        Returns:
            {
                "drifted": bool,
                "regressions": List[str],
                "summary": Dict[str, Any]
            }
        """

        if not self.baseline:
            logger.warning("[DRIFT] No baseline loaded; cannot detect drift")
            return {"drifted": False, "regressions": [], "summary": {}}

        regressions = []
        tier_map = {"LOW": 1, "MODERATE": 2, "SEVERE": 3, "CATASTROPHIC": 4}

        for scenario_id, current in current_results.items():
            if scenario_id not in self.baseline:
                logger.warning("[DRIFT] Scenario %s not in baseline", scenario_id)
                continue

            baseline = self.baseline[scenario_id]

            # Compare risk tier
            baseline_tier = tier_map.get(baseline.get("risk", {}).get("tier", "LOW"), 1)
            current_tier = tier_map.get(current.get("risk", {}).get("tier", "LOW"), 1)
            if current_tier > baseline_tier:
                regressions.append(
                    f"{scenario_id}: Tier worsened ({baseline.get('risk', {}).get('tier')} → {current.get('risk', {}).get('tier')})"
                )

            # Compare aggregate risk
            baseline_agg = float(baseline.get("risk", {}).get("aggregate", 0.0))
            current_agg = float(current.get("risk", {}).get("aggregate", 0.0))
            if current_agg > baseline_agg + max_aggregate_increase:
                regressions.append(f"{scenario_id}: Aggregate risk increased ({baseline_agg:.3f} → {current_agg:.3f})")

            # Compare governance decision
            baseline_decision = baseline.get("governance", {}).get("decision")
            current_decision = current.get("governance", {}).get("decision")
            if baseline_decision == "EXECUTE" and current_decision in {"HALT", "TIER_5_HALT", "FREEZE"}:
                regressions.append(f"{scenario_id}: Governance regressed (EXECUTE → {current_decision})")

        return {
            "drifted": len(regressions) > 0,
            "regressions": regressions,
            "summary": {
                "total_scenarios": len(current_results),
                "baseline_scenarios": len(self.baseline),
                "regression_count": len(regressions),
            },
        }


def run_drift_audit(engine, scenarios: List[Dict[str, Any]], detector: ModelDriftDetector) -> Dict[str, Any]:
    """Execute scenarios and detect drift vs. baseline.

    Args:
        engine: KTEngine instance
        scenarios: List of problem graphs
        detector: ModelDriftDetector with loaded baseline

    Returns:
        Drift audit report
    """

    current_results = {}
    for scenario in scenarios:
        scenario_id = scenario.get("problem_id", "UNKNOWN")
        try:
            result = engine.execute(scenario)
            current_results[scenario_id] = {
                "risk": result.get("risk", {}),
                "governance": result.get("governance", {}),
                "status": result.get("status"),
            }
        except Exception as exc:
            logger.exception("[DRIFT] Scenario %s failed: %s", scenario_id, exc)
            current_results[scenario_id] = {
                "risk": {"tier": "CATASTROPHIC", "aggregate": 1.0, "components": {}},
                "governance": {"decision": "HALT"},
                "status": "ERROR",
                "error": str(exc),
            }

    drift_report = detector.detect_drift(current_results)
    drift_report["current_results"] = current_results
    return drift_report

"""Phase 5 Model Drift Audit Test

Validates:
  - Baseline capture works
  - Drift detection flags tier/aggregate/decision regressions
  - Audit fails when governance degrades
"""

import tempfile
from pathlib import Path

import pytest

from audit.model_drift import ModelDriftDetector, run_drift_audit
from src.core.kt_engine import KTEngine
from tests.phase4_utils import build_problem_graph, configure_stub_student


@pytest.fixture(autouse=True)
def stub_student_kernel(monkeypatch):
    configure_stub_student(monkeypatch)


def test_baseline_capture_and_load():
    """Capture baseline and reload from disk."""

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        detector = ModelDriftDetector(baseline_path=baseline_path)

        scenarios = {
            "SAFE_001": {
                "risk": {"tier": "LOW", "aggregate": 0.05, "components": {}},
                "governance": {"decision": "EXECUTE"},
            },
            "RISKY_001": {
                "risk": {"tier": "MODERATE", "aggregate": 0.25, "components": {}},
                "governance": {"decision": "FREEZE"},
            },
        }

        detector.save_baseline(scenarios)
        assert baseline_path.exists()

        # Reload
        detector2 = ModelDriftDetector(baseline_path=baseline_path)
        assert len(detector2.baseline) == 2
        assert "SAFE_001" in detector2.baseline


def test_drift_detected_when_tier_worsens():
    """Detect drift when risk tier increases."""

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        detector = ModelDriftDetector(baseline_path=baseline_path)

        baseline = {
            "TIER_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.05, "components": {}},
                "governance": {"decision": "EXECUTE"},
            }
        }
        detector.save_baseline(baseline)

        current = {
            "TIER_TEST": {
                "risk": {"tier": "MODERATE", "aggregate": 0.25, "components": {}},
                "governance": {"decision": "EXECUTE"},
            }
        }

        report = detector.detect_drift(current)
        assert report["drifted"] is True
        assert len(report["regressions"]) >= 1
        assert any("Tier worsened" in r for r in report["regressions"])


def test_drift_detected_when_aggregate_increases():
    """Detect drift when aggregate risk exceeds threshold."""

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        detector = ModelDriftDetector(baseline_path=baseline_path)

        baseline = {
            "AGG_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.05, "components": {}},
                "governance": {"decision": "EXECUTE"},
            }
        }
        detector.save_baseline(baseline)

        current = {
            "AGG_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.20, "components": {}},  # +0.15 > threshold
                "governance": {"decision": "EXECUTE"},
            }
        }

        report = detector.detect_drift(current, max_aggregate_increase=0.1)
        assert report["drifted"] is True
        assert any("Aggregate risk increased" in r for r in report["regressions"])


def test_drift_detected_when_governance_regresses():
    """Detect drift when EXECUTE becomes HALT."""

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        detector = ModelDriftDetector(baseline_path=baseline_path)

        baseline = {
            "GOV_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.05, "components": {}},
                "governance": {"decision": "EXECUTE"},
            }
        }
        detector.save_baseline(baseline)

        current = {
            "GOV_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.05, "components": {}},
                "governance": {"decision": "HALT"},
            }
        }

        report = detector.detect_drift(current)
        assert report["drifted"] is True
        assert any("Governance regressed" in r for r in report["regressions"])


def test_no_drift_when_within_tolerance():
    """No drift flagged when changes are within tolerance."""

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        detector = ModelDriftDetector(baseline_path=baseline_path)

        baseline = {
            "STABLE_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.05, "components": {}},
                "governance": {"decision": "EXECUTE"},
            }
        }
        detector.save_baseline(baseline)

        current = {
            "STABLE_TEST": {
                "risk": {"tier": "LOW", "aggregate": 0.08, "components": {}},  # +0.03 < threshold
                "governance": {"decision": "EXECUTE"},
            }
        }

        report = detector.detect_drift(current, max_aggregate_increase=0.1)
        assert report["drifted"] is False
        assert len(report["regressions"]) == 0


def test_run_drift_audit_integration():
    """Full audit workflow with KTEngine."""

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        detector = ModelDriftDetector(baseline_path=baseline_path)
        engine = KTEngine()

        # Define canonical scenarios
        scenarios = [
            build_problem_graph("Safe action A", tags=[]),
            build_problem_graph("Safe action B", tags=[]),
        ]
        scenarios[0]["problem_id"] = "DRIFT_SAFE_A"
        scenarios[1]["problem_id"] = "DRIFT_SAFE_B"

        # Capture baseline
        baseline_report = run_drift_audit(engine, scenarios, detector)
        detector.save_baseline(baseline_report["current_results"])

        # Re-run (should have no drift)
        current_report = run_drift_audit(engine, scenarios, detector)
        assert current_report["drifted"] is False

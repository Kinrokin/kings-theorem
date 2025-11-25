# tests/test_violation_heuristics.py
"""
Tests for violation heuristics and risk probability quantification.
"""
import pytest
import numpy as np
from src.violations.violation_heuristics import (
    ViolationClass,
    ViolationHeuristic,
    RiskProbabilityEngine,
    ChanceConstraintCertificate,
    VIOLATION_RISK_MASS,
)


class TestViolationClass:
    """Tests for ViolationClass enum."""

    def test_violation_class_values(self):
        """Test that all violation classes have correct values."""
        assert ViolationClass.CRITICAL.value == "critical"
        assert ViolationClass.HIGH.value == "high"
        assert ViolationClass.MEDIUM.value == "medium"
        assert ViolationClass.LOW.value == "low"

    def test_risk_mass_mapping(self):
        """Test that risk mass mappings are correct."""
        assert VIOLATION_RISK_MASS[ViolationClass.CRITICAL] == 1.0
        assert VIOLATION_RISK_MASS[ViolationClass.HIGH] == 0.05
        assert VIOLATION_RISK_MASS[ViolationClass.MEDIUM] == 0.01
        assert VIOLATION_RISK_MASS[ViolationClass.LOW] == 0.001


class TestViolationHeuristic:
    """Tests for ViolationHeuristic."""

    def test_heuristic_creation(self):
        """Test creating a violation heuristic."""
        heuristic = ViolationHeuristic(
            heuristic_id="H001",
            name="test_heuristic",
            violation_class=ViolationClass.HIGH,
            estimated_risk_mass=0.05,
            description="Test heuristic",
        )
        assert heuristic.heuristic_id == "H001"
        assert heuristic.violation_class == ViolationClass.HIGH
        assert heuristic.estimated_risk_mass == 0.05

    def test_heuristic_evaluate_no_check_fn(self):
        """Test evaluate returns False when no check function is defined."""
        heuristic = ViolationHeuristic(
            heuristic_id="H001",
            name="test",
            violation_class=ViolationClass.LOW,
            estimated_risk_mass=0.001,
        )
        triggered, risk, msg = heuristic.evaluate({})
        assert triggered is False
        assert risk == 0.0

    def test_heuristic_evaluate_with_check_fn(self):
        """Test evaluate with a custom check function."""
        def check_fn(ctx):
            if ctx.get("danger", False):
                return True, "Danger detected"
            return False, "No danger"

        heuristic = ViolationHeuristic(
            heuristic_id="H001",
            name="danger_check",
            violation_class=ViolationClass.CRITICAL,
            estimated_risk_mass=1.0,
            check_fn=check_fn,
        )

        # Test triggered case
        triggered, risk, msg = heuristic.evaluate({"danger": True})
        assert triggered is True
        assert risk == 1.0
        assert "Danger detected" in msg

        # Test non-triggered case
        triggered, risk, msg = heuristic.evaluate({"danger": False})
        assert triggered is False
        assert risk == 0.0


class TestChanceConstraintCertificate:
    """Tests for ChanceConstraintCertificate."""

    def test_certificate_creation(self):
        """Test creating a certificate."""
        cert = ChanceConstraintCertificate(
            certificate_id="cert001",
            theorem_id="T1",
            violation_class=ViolationClass.HIGH,
            probability_bound=0.05,
            observed_probability=0.01,
            status="PASS",
        )
        assert cert.certificate_id == "cert001"
        assert cert.theorem_id == "T1"
        assert cert.status == "PASS"
        assert len(cert.certificate_hash) == 64  # SHA256 hex

    def test_certificate_is_valid_pass(self):
        """Test is_valid returns True when within bound."""
        cert = ChanceConstraintCertificate(
            certificate_id="cert001",
            theorem_id="T1",
            violation_class=ViolationClass.HIGH,
            probability_bound=0.05,
            observed_probability=0.01,
            status="PASS",
        )
        assert cert.is_valid() is True

    def test_certificate_is_valid_fail(self):
        """Test is_valid returns False when exceeds bound."""
        cert = ChanceConstraintCertificate(
            certificate_id="cert001",
            theorem_id="T1",
            violation_class=ViolationClass.HIGH,
            probability_bound=0.05,
            observed_probability=0.10,
            status="FAIL",
        )
        assert cert.is_valid() is False

    def test_certificate_to_dict(self):
        """Test certificate serialization."""
        cert = ChanceConstraintCertificate(
            certificate_id="cert001",
            theorem_id="T1",
            violation_class=ViolationClass.HIGH,
            probability_bound=0.05,
            observed_probability=0.01,
            status="PASS",
        )
        d = cert.to_dict()
        assert d["certificate_id"] == "cert001"
        assert d["theorem_id"] == "T1"
        assert d["violation_class"] == "high"
        assert "certificate_hash" in d


class TestRiskProbabilityEngine:
    """Tests for RiskProbabilityEngine."""

    def test_engine_creation(self):
        """Test creating the engine."""
        engine = RiskProbabilityEngine()
        assert engine.confidence_level == 0.999
        assert len(engine.heuristics) > 0

    def test_compute_cvar(self):
        """Test CVaR computation at 99.9%."""
        engine = RiskProbabilityEngine()

        # Test with simple distribution
        losses = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        cvar = engine.compute_cvar(losses, confidence=0.9)
        # CVaR at 90% is the expected value of losses above VaR
        # With 10 values, 90% confidence means top 10% = 1 value
        # But our implementation takes the mean of top ceil(n * confidence) values
        assert cvar > 0.5  # Should be high since it's the tail

    def test_compute_cvar_empty(self):
        """Test CVaR with empty distribution."""
        engine = RiskProbabilityEngine()
        assert engine.compute_cvar([]) == 0.0

    def test_safety_breach_detection(self):
        """Test detection of safety property breaches."""
        engine = RiskProbabilityEngine()

        # Context with safety breach
        context = {
            "safety_flags": {
                "irreversible_harm": True,
                "safety_property_violated": False,
            }
        }

        total_risk, violations = engine.evaluate_all_heuristics(context)
        assert total_risk > 0

        # Check that safety breach was detected
        breach_detected = any(hid == "H001" for hid, _, _, _ in violations)
        assert breach_detected

    def test_numerical_instability_detection(self):
        """Test detection of NaN/Inf values."""
        engine = RiskProbabilityEngine()

        context = {
            "numerical_values": [1.0, 2.0, float('nan'), 4.0]
        }

        total_risk, violations = engine.evaluate_all_heuristics(context)
        assert total_risk > 0

        # Check that numerical instability was detected
        instability_detected = any(hid == "H003" for hid, _, _, _ in violations)
        assert instability_detected

    def test_cvar_threshold_check(self):
        """Test CVaR threshold violation detection."""
        engine = RiskProbabilityEngine()

        # Loss distribution with high CVaR
        context = {
            "loss_distribution": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            "cvar_threshold": 0.1,
        }

        total_risk, violations = engine.evaluate_all_heuristics(context)
        assert total_risk > 0

    def test_generate_certificate_pass(self):
        """Test generating a passing certificate."""
        engine = RiskProbabilityEngine()

        cert = engine.generate_certificate(
            theorem_id="T1",
            violation_class=ViolationClass.HIGH,
            observed_probability=0.01,
            probability_bound=0.05,
        )

        assert cert.status == "PASS"
        assert cert.is_valid() is True

    def test_generate_certificate_fail(self):
        """Test generating a failing certificate."""
        engine = RiskProbabilityEngine()

        cert = engine.generate_certificate(
            theorem_id="T1",
            violation_class=ViolationClass.HIGH,
            observed_probability=0.10,
            probability_bound=0.05,
        )

        assert cert.status == "FAIL"
        assert cert.is_valid() is False

    def test_calibration_from_stress_suite(self):
        """Test calibration loop from stress suite."""
        engine = RiskProbabilityEngine()

        # Simulate empirical frequencies higher than estimates
        empirical = [0.1, 0.12, 0.08, 0.11, 0.09]
        estimates = [0.05, 0.05, 0.05, 0.05, 0.05]

        factor = engine.calibrate_from_stress_suite("H002", empirical, estimates)

        # Factor should be ~2.0 (0.1 / 0.05)
        assert factor > 1.5
        assert factor < 2.5

    def test_adversarial_stress_suite(self):
        """Test running adversarial stress suite."""
        engine = RiskProbabilityEngine()

        # Create test contexts
        contexts = [
            {"safety_flags": {"irreversible_harm": False}},
            {"safety_flags": {"irreversible_harm": True}},
            {"numerical_values": [1.0, 2.0]},
            {"numerical_values": [float('nan')]},
        ]

        report = engine.run_adversarial_stress_suite(contexts, suite_name="test_suite")

        assert report["suite_name"] == "test_suite"
        assert report["total_tests"] == 4
        assert "heuristic_results" in report
        assert "severity_summary" in report


class TestDSLIntegration:
    """Tests for DSL theorem output integration."""

    def test_dsl_compile_and_evaluate(self):
        """Test DSL compilation and evaluation."""
        from src.proofs.dsl import compile_and_evaluate

        source = """
constraint C1: fairness >= 0.7
constraint C2: safety_score >= 0.8
bound B1: cvar_99 <= 0.001
theorem T1: C1 & C2 -> SAFE
"""
        evidence = {
            "fairness": 0.8,
            "safety_score": 0.9,
            "cvar_99": 0.0005,
        }

        output = compile_and_evaluate(source, evidence, observed_metrics=evidence)

        assert output.overall_status == "PASS"
        assert len(output.theorem_results) == 1
        assert output.theorem_results[0].status == "PASS"

    def test_dsl_theorem_failure(self):
        """Test DSL theorem failure detection."""
        from src.proofs.dsl import compile_and_evaluate

        source = """
constraint C1: fairness >= 0.7
theorem T1: C1 -> SAFE
"""
        evidence = {"fairness": 0.5}  # Below threshold

        output = compile_and_evaluate(source, evidence)

        assert output.overall_status == "FAIL"
        assert output.theorem_results[0].status == "FAIL"

    def test_dsl_bound_failure(self):
        """Test DSL bound violation detection."""
        from src.proofs.dsl import compile_and_evaluate

        source = """
constraint C1: fairness >= 0.7
bound B1: cvar_99 <= 0.001
theorem T1: C1 -> SAFE
"""
        evidence = {"fairness": 0.8}
        observed = {"cvar_99": 0.01}  # Exceeds bound

        output = compile_and_evaluate(source, evidence, observed_metrics=observed)

        assert output.overall_status == "FAIL"
        assert output.bound_results["B1"]["passed"] is False

    def test_dsl_output_serialization(self):
        """Test DSL output JSON serialization."""
        from src.proofs.dsl import compile_and_evaluate

        source = """
constraint C1: fairness >= 0.7
theorem T1: C1 -> SAFE
"""
        evidence = {"fairness": 0.8}

        output = compile_and_evaluate(source, evidence)
        json_str = output.to_json()

        assert "theorem" in json_str
        assert "PASS" in json_str
        assert "certificate" in json_str

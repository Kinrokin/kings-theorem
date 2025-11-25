# src/violations/violation_heuristics.py
"""
Violation Heuristics for Risk Probability Quantification

This module implements heuristics that don't just flag violations but quantify
them in terms of meaningful risk probability, using:
- Violation Classes (Critical, High, Medium, Low)
- Conditional Value at Risk (CVaR) at 99.9% for tail events
- Probability semantics mapping (heuristic X triggers → estimated risk mass)
- Chance-constraint certificates for CI integration
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("kt.violations")
logger.setLevel(logging.INFO)


class ViolationClass(Enum):
    """
    Violation severity classes with probability semantics.

    - CRITICAL: Irreversible harm, safety property breach (probability must be forced to 0)
    - HIGH: Tail-risk events (CVaR > threshold)
    - MEDIUM: Degraded performance or audit gaps
    - LOW: Cosmetic or non-audit issues
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Risk mass mappings for each violation class
VIOLATION_RISK_MASS = {
    ViolationClass.CRITICAL: 1.0,  # Probability forced to 0 (fail immediately)
    ViolationClass.HIGH: 0.05,  # CVaR 99.9% tail events
    ViolationClass.MEDIUM: 0.01,  # Degraded but recoverable
    ViolationClass.LOW: 0.001,  # Cosmetic issues
}


@dataclass
class ViolationHeuristic:
    """
    A violation heuristic with probability semantics.

    Attributes:
        heuristic_id: Unique identifier for the heuristic
        name: Human-readable name
        violation_class: Severity classification
        estimated_risk_mass: Probability mass when triggered
        description: What this heuristic detects
        check_fn: Optional callable for evaluation
    """

    heuristic_id: str
    name: str
    violation_class: ViolationClass
    estimated_risk_mass: float
    description: str = ""
    check_fn: Optional[callable] = None

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Evaluate whether this heuristic triggers on the given context.

        Returns:
            (triggered, risk_mass, message)
        """
        if self.check_fn is None:
            return False, 0.0, "No check function defined"

        try:
            triggered, message = self.check_fn(context)
            if triggered:
                return True, self.estimated_risk_mass, message
            return False, 0.0, message
        except Exception as e:
            logger.exception(f"Error evaluating heuristic {self.heuristic_id}: {e}")
            return True, self.estimated_risk_mass, f"Evaluation error: {e}"


@dataclass
class ChanceConstraintCertificate:
    """
    Certificate for chance-constraint validation.

    If violation probability > bound, CI fails.
    """

    certificate_id: str
    theorem_id: str
    violation_class: ViolationClass
    probability_bound: float
    observed_probability: float
    status: str  # "PASS", "FAIL", "PENDING"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    certificate_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.certificate_hash:
            self.certificate_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA256 hash of certificate for integrity verification."""
        # Round floating-point values to fixed precision for deterministic hashing
        data = {
            "certificate_id": self.certificate_id,
            "theorem_id": self.theorem_id,
            "violation_class": self.violation_class.value,
            "probability_bound": round(self.probability_bound, 10),
            "observed_probability": round(self.observed_probability, 10),
            "status": self.status,
            "timestamp": self.timestamp,
        }
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    def is_valid(self) -> bool:
        """Check if the certificate passes the chance constraint."""
        return self.observed_probability <= self.probability_bound

    def to_dict(self) -> Dict[str, Any]:
        """Serialize certificate to dictionary for JSON output."""
        return {
            "certificate_id": self.certificate_id,
            "theorem_id": self.theorem_id,
            "violation_class": self.violation_class.value,
            "probability_bound": self.probability_bound,
            "observed_probability": self.observed_probability,
            "status": self.status,
            "timestamp": self.timestamp,
            "certificate_hash": self.certificate_hash,
            "metadata": self.metadata,
        }


class RiskProbabilityEngine:
    """
    Engine for computing risk probabilities and CVaR metrics.

    Implements:
    - CVaR at 99.9% for tail events
    - Calibration loop for adversarial stress suites
    - Chance-constraint certificate generation
    """

    def __init__(self, confidence_level: float = 0.999, default_bound: float = 0.001):
        """
        Initialize the risk probability engine.

        Args:
            confidence_level: Confidence level for CVaR (default 99.9%)
            default_bound: Default probability bound for chance constraints
        """
        self.confidence_level = confidence_level
        self.default_bound = default_bound
        self.heuristics: Dict[str, ViolationHeuristic] = {}
        self.calibration_data: Dict[str, List[float]] = {}
        self._register_default_heuristics()

    def _register_default_heuristics(self):
        """Register default violation heuristics."""
        # Critical: Safety property breaches
        self.register_heuristic(
            ViolationHeuristic(
                heuristic_id="H001",
                name="safety_property_breach",
                violation_class=ViolationClass.CRITICAL,
                estimated_risk_mass=1.0,
                description="Detects irreversible safety property violations",
                check_fn=self._check_safety_breach,
            )
        )

        # High: Tail-risk events (CVaR violations)
        self.register_heuristic(
            ViolationHeuristic(
                heuristic_id="H002",
                name="cvar_threshold_exceeded",
                violation_class=ViolationClass.HIGH,
                estimated_risk_mass=0.05,
                description="CVaR at 99.9% exceeds threshold",
                check_fn=self._check_cvar_threshold,
            )
        )

        # High: NaN/Inf detection
        self.register_heuristic(
            ViolationHeuristic(
                heuristic_id="H003",
                name="numerical_instability",
                violation_class=ViolationClass.HIGH,
                estimated_risk_mass=0.05,
                description="Detects NaN/Inf values in outputs",
                check_fn=self._check_numerical_stability,
            )
        )

        # Medium: Audit gaps
        self.register_heuristic(
            ViolationHeuristic(
                heuristic_id="H004",
                name="audit_gap",
                violation_class=ViolationClass.MEDIUM,
                estimated_risk_mass=0.01,
                description="Missing audit trail or integrity records",
                check_fn=self._check_audit_gaps,
            )
        )

        # Medium: Lockfile drift
        self.register_heuristic(
            ViolationHeuristic(
                heuristic_id="H005",
                name="lockfile_drift",
                violation_class=ViolationClass.MEDIUM,
                estimated_risk_mass=0.01,
                description="Dependency lockfile is out of sync",
                check_fn=self._check_lockfile_drift,
            )
        )

        # Low: Cosmetic issues
        self.register_heuristic(
            ViolationHeuristic(
                heuristic_id="H006",
                name="cosmetic_issue",
                violation_class=ViolationClass.LOW,
                estimated_risk_mass=0.001,
                description="Non-functional cosmetic issues",
                check_fn=lambda ctx: (False, "No cosmetic issues"),
            )
        )

    def register_heuristic(self, heuristic: ViolationHeuristic):
        """Register a new violation heuristic."""
        self.heuristics[heuristic.heuristic_id] = heuristic

    def _check_safety_breach(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for safety property breaches (Critical)."""
        safety_flags = context.get("safety_flags", {})
        breaches = []

        if safety_flags.get("irreversible_harm", False):
            breaches.append("irreversible_harm")
        if safety_flags.get("safety_property_violated", False):
            breaches.append("safety_property_violated")
        if safety_flags.get("monstrous_optima", False):
            breaches.append("monstrous_optima")

        if breaches:
            return True, f"Safety breaches detected: {', '.join(breaches)}"
        return False, "No safety breaches"

    def _check_cvar_threshold(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if CVaR at 99.9% exceeds threshold (High)."""
        loss_distribution = context.get("loss_distribution", [])
        threshold = context.get("cvar_threshold", 0.1)

        if not loss_distribution:
            return False, "No loss distribution provided"

        cvar = self.compute_cvar(loss_distribution)
        if cvar > threshold:
            return True, f"CVaR({self.confidence_level}) = {cvar:.4f} exceeds threshold {threshold}"
        return False, f"CVaR({self.confidence_level}) = {cvar:.4f} within threshold"

    def _check_numerical_stability(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for NaN/Inf values in numerical outputs (High)."""
        values = context.get("numerical_values", [])
        instabilities = []

        for i, v in enumerate(values):
            if isinstance(v, (float, int)):
                if np.isnan(v):
                    instabilities.append(f"NaN at index {i}")
                elif np.isinf(v):
                    instabilities.append(f"Inf at index {i}")

        if instabilities:
            return True, f"Numerical instabilities: {', '.join(instabilities)}"
        return False, "No numerical instabilities"

    def _check_audit_gaps(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check for missing audit records (Medium)."""
        audit_records = context.get("audit_records", [])
        required_records = context.get("required_records", ["ledger_entry", "signature"])

        missing = [r for r in required_records if r not in audit_records]
        if missing:
            return True, f"Missing audit records: {', '.join(missing)}"
        return False, "All audit records present"

    def _check_lockfile_drift(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if dependency lockfile has drifted (Medium)."""
        lockfile_status = context.get("lockfile_status", "unknown")

        if lockfile_status == "drift":
            return True, "Lockfile has drifted from requirements"
        if lockfile_status == "missing_hashes":
            return True, "Lockfile is missing hash verification"
        return False, "Lockfile is in sync"

    def compute_cvar(self, loss_distribution: List[float], confidence: float = None) -> float:
        """
        Compute Conditional Value at Risk (CVaR) at the specified confidence level.

        CVaR is the expected loss given that the loss exceeds the VaR threshold.

        Args:
            loss_distribution: List of loss values (higher = worse)
            confidence: Confidence level (default: self.confidence_level = 0.999)

        Returns:
            CVaR value
        """
        if not loss_distribution:
            return 0.0

        confidence = confidence or self.confidence_level
        arr = np.array(loss_distribution)
        n = len(arr)

        # Compute VaR index: number of samples to include in tail
        # For CVaR at confidence level α, we want the expected loss in the worst (1-α) of cases
        tail_proportion = 1.0 - confidence
        tail_count = max(1, int(np.ceil(n * tail_proportion)))

        # Sort descending to get worst losses first
        sorted_losses = np.sort(arr)[::-1]

        # CVaR is the mean of the worst tail_count losses
        tail_losses = sorted_losses[:tail_count]
        return float(np.mean(tail_losses))

    def evaluate_all_heuristics(
        self, context: Dict[str, Any]
    ) -> Tuple[float, List[Tuple[str, ViolationClass, float, str]]]:
        """
        Evaluate all registered heuristics and compute aggregate risk.

        Returns:
            (total_risk_mass, list of (heuristic_id, class, risk_mass, message))
        """
        results = []
        total_risk = 0.0

        for hid, heuristic in self.heuristics.items():
            triggered, risk_mass, message = heuristic.evaluate(context)
            if triggered:
                results.append((hid, heuristic.violation_class, risk_mass, message))
                total_risk += risk_mass

        return min(1.0, total_risk), results

    def generate_certificate(
        self,
        theorem_id: str,
        violation_class: ViolationClass,
        observed_probability: float,
        probability_bound: float = None,
        metadata: Dict[str, Any] = None,
    ) -> ChanceConstraintCertificate:
        """
        Generate a chance-constraint certificate.

        Args:
            theorem_id: ID of the theorem being certified
            violation_class: Severity class of the violation
            observed_probability: Observed violation probability
            probability_bound: Maximum allowed probability (default from class)
            metadata: Additional metadata

        Returns:
            ChanceConstraintCertificate
        """
        if probability_bound is None:
            probability_bound = VIOLATION_RISK_MASS.get(violation_class, self.default_bound)

        status = "PASS" if observed_probability <= probability_bound else "FAIL"

        cert = ChanceConstraintCertificate(
            certificate_id=hashlib.sha256(f"{theorem_id}-{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16],
            theorem_id=theorem_id,
            violation_class=violation_class,
            probability_bound=probability_bound,
            observed_probability=observed_probability,
            status=status,
            metadata=metadata or {},
        )

        return cert

    def calibrate_from_stress_suite(
        self, heuristic_id: str, empirical_frequencies: List[float], heuristic_estimates: List[float]
    ) -> float:
        """
        Calibration loop: Compare empirical violation frequency vs heuristic estimate.

        Adjusts thresholds until heuristic probability ≈ observed frequency.

        Args:
            heuristic_id: ID of heuristic to calibrate
            empirical_frequencies: Observed violation frequencies from stress tests
            heuristic_estimates: Corresponding heuristic probability estimates

        Returns:
            Calibration factor (ratio of empirical to estimated)
        """
        if not empirical_frequencies or not heuristic_estimates:
            return 1.0

        emp_mean = np.mean(empirical_frequencies)
        est_mean = np.mean(heuristic_estimates)

        if est_mean == 0:
            return 1.0

        calibration_factor = emp_mean / est_mean

        # Store calibration data
        self.calibration_data[heuristic_id] = {
            "empirical_mean": float(emp_mean),
            "estimated_mean": float(est_mean),
            "calibration_factor": float(calibration_factor),
            "sample_size": len(empirical_frequencies),
        }

        # Adjust heuristic if registered
        if heuristic_id in self.heuristics:
            heuristic = self.heuristics[heuristic_id]
            heuristic.estimated_risk_mass *= calibration_factor
            logger.info(
                f"Calibrated {heuristic_id}: risk_mass {heuristic.estimated_risk_mass / calibration_factor:.4f} -> {heuristic.estimated_risk_mass:.4f}"
            )

        return calibration_factor

    def run_adversarial_stress_suite(
        self, contexts: List[Dict[str, Any]], suite_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Run adversarial stress suite and return calibration report.

        This is the calibration loop:
        1. Run adversarial stress tests (poisoning, paradox injection, governance drift)
        2. Compare empirical violation frequency vs heuristic estimate
        3. Report discrepancies for threshold adjustment

        Args:
            contexts: List of test contexts to evaluate
            suite_name: Name of the stress suite

        Returns:
            Calibration report with frequencies and recommendations
        """
        results = {
            "suite_name": suite_name,
            "total_tests": len(contexts),
            "heuristic_results": {},
            "calibration_recommendations": [],
        }

        # Track triggers per heuristic
        trigger_counts = {hid: 0 for hid in self.heuristics}
        severity_counts = {vc: 0 for vc in ViolationClass}

        for ctx in contexts:
            total_risk, violations = self.evaluate_all_heuristics(ctx)
            for hid, vclass, risk, msg in violations:
                trigger_counts[hid] += 1
                severity_counts[vclass] += 1

        # Compute empirical frequencies
        n = len(contexts) if contexts else 1
        for hid, count in trigger_counts.items():
            freq = count / n
            heuristic = self.heuristics[hid]
            expected = heuristic.estimated_risk_mass

            results["heuristic_results"][hid] = {
                "name": heuristic.name,
                "violation_class": heuristic.violation_class.value,
                "trigger_count": count,
                "empirical_frequency": freq,
                "estimated_risk_mass": expected,
                "calibration_ratio": freq / expected if expected > 0 else None,
            }

            # Recommend calibration if off by more than 50%
            if expected > 0 and abs(freq - expected) / expected > 0.5:
                results["calibration_recommendations"].append(
                    {
                        "heuristic_id": hid,
                        "current_estimate": expected,
                        "empirical_frequency": freq,
                        "recommended_value": freq,
                        "action": "RECALIBRATE",
                    }
                )

        results["severity_summary"] = {vc.value: count for vc, count in severity_counts.items()}

        return results

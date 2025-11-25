"""Minimal Proof DSL Skeleton

Supports declaring constraints and a simple theorem form:

constraint C1: fairness >= 0.7
constraint C2: traditions >= 2
theorem T1: C1 & C2 -> COMPOSITION_SAFE

Evaluation checks provided evidence dict for required constraint satisfaction.
This is a placeholder to evolve into a richer DSL.

Extended for CI Gating:
- Emits machine-readable JSON/YAML artifacts with risk bounds
- Generates certificates with proof hashes
- Supports CI integration with threshold enforcement
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


CONSTRAINT_RE = re.compile(r"^constraint\s+(?P<cid>[A-Za-z0-9_]+):\s*(?P<body>.+)$")
THEOREM_RE = re.compile(r"^theorem\s+(?P<tid>[A-Za-z0-9_]+):\s*(?P<body>.+)$")
# Extended patterns for risk bounds
BOUND_RE = re.compile(r"^bound\s+(?P<bid>[A-Za-z0-9_]+):\s*(?P<metric>[A-Za-z0-9_]+)\s*(?P<op><=|>=|<|>|==)\s*(?P<val>[0-9]*\.?[0-9]+)$")


@dataclass
class Constraint:
    cid: str
    expr: str  # e.g. fairness >= 0.7

    def evaluate(self, evidence: Dict[str, float]) -> bool:
        # VERY minimal parser: metric OP value
        m = re.match(r"^(?P<metric>[A-Za-z0-9_]+)\s*(>=|<=|>|<|==)\s*(?P<val>[0-9]*\.?[0-9]+)$", self.expr)
        if not m:
            return False
        metric = m.group("metric")
        op = m.group(2)
        val = float(m.group("val"))
        actual = float(evidence.get(metric, 0.0))
        if op == ">=":
            return actual >= val
        if op == "<=":
            return actual <= val
        if op == ">":
            return actual > val
        if op == "<":
            return actual < val
        if op == "==":
            return abs(actual - val) < 1e-9
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize constraint to dictionary."""
        return {"id": self.cid, "expression": self.expr}


@dataclass
class RiskBound:
    """Risk bound specification for CI gating."""

    bid: str
    metric: str
    operator: str
    value: float

    def check(self, observed_value: float) -> bool:
        """Check if observed value satisfies the bound."""
        if self.operator == "<=":
            return observed_value <= self.value
        if self.operator == ">=":
            return observed_value >= self.value
        if self.operator == "<":
            return observed_value < self.value
        if self.operator == ">":
            return observed_value > self.value
        if self.operator == "==":
            return abs(observed_value - self.value) < 1e-9
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize bound to dictionary."""
        return {"id": self.bid, "metric": self.metric, "operator": self.operator, "value": self.value}


@dataclass
class Theorem:
    tid: str
    antecedents: List[str]  # constraint ids
    consequent: str  # symbolic label only

    def check(self, constraints: Dict[str, Constraint], evidence: Dict[str, float]) -> bool:
        return all(constraints[cid].evaluate(evidence) for cid in self.antecedents)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize theorem to dictionary."""
        return {"id": self.tid, "antecedents": self.antecedents, "consequent": self.consequent}


@dataclass
class ProofProgram:
    constraints: Dict[str, Constraint]
    theorems: Dict[str, Theorem]
    bounds: Dict[str, RiskBound] = field(default_factory=dict)

    def evaluate(self, evidence: Dict[str, float]) -> Dict[str, bool]:
        results = {}
        for tid, th in self.theorems.items():
            results[tid] = th.check(self.constraints, evidence)
        return results

    def check_bounds(self, observed: Dict[str, float]) -> Dict[str, bool]:
        """Check all risk bounds against observed values."""
        results = {}
        for bid, bound in self.bounds.items():
            obs = observed.get(bound.metric, 0.0)
            results[bid] = bound.check(obs)
        return results


@dataclass
class TheoremResult:
    """Result of evaluating a single theorem."""

    theorem_id: str
    status: str  # "PASS", "FAIL", "PENDING"
    bound: Optional[float] = None
    observed: Optional[float] = None
    certificate_hash: str = ""
    antecedents_status: Dict[str, bool] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self):
        if not self.certificate_hash:
            self.certificate_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute certificate hash for integrity."""
        data = {
            "theorem_id": self.theorem_id,
            "status": self.status,
            "bound": self.bound,
            "observed": self.observed,
            "antecedents_status": self.antecedents_status,
        }
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "theorem": self.theorem_id,
            "status": self.status,
            "bound": self.bound,
            "observed": self.observed,
            "certificate": self.certificate_hash,
            "antecedents_status": self.antecedents_status,
            "message": self.message,
        }


@dataclass
class DSLCompilerOutput:
    """Machine-readable output from DSL compiler for CI gating."""

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    program_hash: str = ""
    theorem_results: List[TheoremResult] = field(default_factory=list)
    bound_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_status: str = "PENDING"
    violation_probability: float = 0.0
    safety_verdict: str = "UNKNOWN"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def all_passed(self) -> bool:
        """Check if all theorems and bounds passed."""
        for tr in self.theorem_results:
            if tr.status == "FAIL":
                return False
        for bid, br in self.bound_results.items():
            if not br.get("passed", True):
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {
            "timestamp": self.timestamp,
            "program_hash": self.program_hash,
            "theorems": [tr.to_dict() for tr in self.theorem_results],
            "bounds": self.bound_results,
            "overall_status": self.overall_status,
            "violation_probability": self.violation_probability,
            "safety_verdict": self.safety_verdict,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        try:
            import yaml

            return yaml.safe_dump(self.to_dict(), default_flow_style=False)
        except ImportError:
            # Fallback to JSON if yaml not available
            return self.to_json()

    def save(self, path: str, format: str = "json") -> None:
        """Save output to file."""
        p = Path(path)
        if format == "yaml":
            p.write_text(self.to_yaml())
        else:
            p.write_text(self.to_json())


def parse(source: str) -> ProofProgram:
    constraints: Dict[str, Constraint] = {}
    theorems: Dict[str, Theorem] = {}
    bounds: Dict[str, RiskBound] = {}

    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse constraint
        mc = CONSTRAINT_RE.match(line)
        if mc:
            cid = mc.group("cid")
            body = mc.group("body")
            constraints[cid] = Constraint(cid, body)
            continue

        # Parse theorem
        mt = THEOREM_RE.match(line)
        if mt:
            tid = mt.group("tid")
            body = mt.group("body")
            # parse simple form: C1 & C2 -> LABEL
            if "->" not in body:
                continue
            antecedent_part, consequent_part = body.split("->", 1)
            antecedents = [a.strip() for a in antecedent_part.split("&")]
            theorems[tid] = Theorem(tid, antecedents, consequent_part.strip())
            continue

        # Parse bound
        mb = BOUND_RE.match(line)
        if mb:
            bid = mb.group("bid")
            metric = mb.group("metric")
            op = mb.group("op")
            val = float(mb.group("val"))
            bounds[bid] = RiskBound(bid, metric, op, val)

    return ProofProgram(constraints, theorems, bounds)


def quick_demo():
    src = """\nconstraint C1: fairness >= 0.7\nconstraint C2: traditions >= 2\ntheorem T1: C1 & C2 -> COMPOSITION_SAFE\n"""
    program = parse(src)
    evidence = {"fairness": 0.75, "traditions": 3}
    return program.evaluate(evidence)


def compile_and_evaluate(
    source: str, evidence: Dict[str, float], observed_metrics: Dict[str, float] = None, thresholds: Dict[str, float] = None
) -> DSLCompilerOutput:
    """
    Compile DSL source and evaluate against evidence.

    This is the main entry point for CI integration.

    Args:
        source: DSL source code
        evidence: Evidence dictionary for constraint evaluation
        observed_metrics: Observed metric values for bound checking
        thresholds: Threshold overrides for CI gating

    Returns:
        DSLCompilerOutput with machine-readable results
    """
    program = parse(source)
    observed_metrics = observed_metrics or {}
    thresholds = thresholds or {}

    # Compute program hash
    program_hash = hashlib.sha256(source.encode()).hexdigest()

    output = DSLCompilerOutput(program_hash=program_hash)

    # Evaluate theorems
    theorem_results = program.evaluate(evidence)
    failed_count = 0

    for tid, passed in theorem_results.items():
        theorem = program.theorems[tid]
        antecedent_status = {cid: program.constraints[cid].evaluate(evidence) for cid in theorem.antecedents}

        tr = TheoremResult(
            theorem_id=tid,
            status="PASS" if passed else "FAIL",
            antecedents_status=antecedent_status,
            message=f"Theorem {tid} {'passed' if passed else 'failed'}",
        )
        output.theorem_results.append(tr)
        if not passed:
            failed_count += 1

    # Evaluate bounds
    bound_results = program.check_bounds(observed_metrics)
    for bid, passed in bound_results.items():
        bound = program.bounds[bid]
        obs = observed_metrics.get(bound.metric, 0.0)

        # Apply threshold override if provided
        threshold = thresholds.get(bid, bound.value)
        if threshold == bound.value:
            threshold_passed = bound.check(obs)
        else:
            # Use threshold override with same operator semantics
            if bound.operator in ["<=", "<"]:
                threshold_passed = obs <= threshold if bound.operator == "<=" else obs < threshold
            else:
                threshold_passed = obs >= threshold if bound.operator == ">=" else obs > threshold

        output.bound_results[bid] = {
            "metric": bound.metric,
            "operator": bound.operator,
            "bound": bound.value,
            "threshold": threshold,
            "observed": obs,
            "passed": threshold_passed,
        }
        if not threshold_passed:
            failed_count += 1

    # Compute overall status
    if failed_count == 0:
        output.overall_status = "PASS"
        output.safety_verdict = "SAFE"
    else:
        output.overall_status = "FAIL"
        output.safety_verdict = "UNSAFE"

    # Compute violation probability estimate
    total_checks = len(theorem_results) + len(bound_results)
    output.violation_probability = failed_count / total_checks if total_checks > 0 else 0.0

    return output


def verify_theorem_output(
    output: DSLCompilerOutput, max_violation_probability: float = 0.001, require_all_pass: bool = True
) -> bool:
    """
    Verify DSL compiler output for CI gating.

    Args:
        output: DSLCompilerOutput to verify
        max_violation_probability: Maximum allowed violation probability
        require_all_pass: If True, all theorems and bounds must pass

    Returns:
        True if verification passes, False otherwise (CI should fail)
    """
    if require_all_pass and not output.all_passed():
        return False

    if output.violation_probability > max_violation_probability:
        return False

    if output.overall_status == "FAIL":
        return False

    return True


if __name__ == "__main__":
    print(quick_demo())

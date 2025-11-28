"""Constraint Lattice (Phase 2)

Unified file containing both heuristic parse helpers (for Phoenix wiring)
and the existing richer Constraint/ConstraintLattice abstractions used by
the counterfactual engine. Duplicate functionality intentionally merged.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .conflict_matrix import check_conflict

# --- Heuristic section (Phoenix) ---
RISK_PATTERN = re.compile(r"RISK\s*<\s*(\d+)(?:%?)", re.IGNORECASE)


def parse(problem: Dict[str, Any]) -> Dict[str, Any]:
    text = str(problem.get("constraint", ""))
    risk_matches = RISK_PATTERN.findall(text)
    risk_bounds = [int(m) for m in risk_matches]
    profit = "MAXIMIZE PROFIT" in text.upper()
    zero_risk = "RISK=0" in text.upper() or "ZERO RISK" in text.upper()
    return {
        "raw": text,
        "risk_bounds": risk_bounds,
        "profit_goal": profit,
        "zero_risk": zero_risk,
    }


def meet(c1: Dict[str, Any], c2: Dict[str, Any]) -> Dict[str, Any]:
    b1 = c1.get("risk_bounds", [])
    b2 = c2.get("risk_bounds", [])
    chosen = []
    if b1 or b2:
        combined = b1 + b2
        chosen = [min(combined)]
    return {
        "risk_bounds": chosen,
        "profit_goal": c1.get("profit_goal") or c2.get("profit_goal"),
        "zero_risk": c1.get("zero_risk") or c2.get("zero_risk"),
    }


def is_composable(constraints_list: List[Dict[str, Any]]) -> bool:
    profit = any(c.get("profit_goal") for c in constraints_list)
    zero_risk = any(c.get("zero_risk") for c in constraints_list)
    return not (profit and zero_risk)


def verify(solution: Dict[str, Any], lattice_constraints: Dict[str, Any]) -> bool:
    if not isinstance(solution, dict):
        return False
    outcome = solution.get("outcome") or solution.get("status")
    if outcome and str(outcome).upper() in {"VETOED", "FAILED"}:
        return True
    bounds = lattice_constraints.get("risk_bounds", [])
    if not bounds:
        return True
    strict_bound = min(bounds)
    gov = solution.get("governance") or {}
    risk_score = gov.get("risk_score")
    if risk_score is None:
        return True
    threshold = strict_bound / 100.0
    return risk_score <= threshold


# --- Rich lattice section (legacy engine dependencies) ---


class ConstraintType(Enum):
    SAFETY = "safety"
    OPERATIONAL = "operational"
    EPISTEMIC = "epistemic"
    PRUDENTIAL = "prudential"
    ETHICAL = "ethical"


@dataclass(frozen=True)
class Constraint:
    id: str
    type: ConstraintType
    expression: str
    strength: float
    domain: str
    proof_obligation: bool = False

    def as_json(self):
        return {
            "id": self.id,
            "type": self.type.value,
            "expression": self.expression,
            "strength": self.strength,
            "domain": self.domain,
            "proof_obligation": self.proof_obligation,
        }


def canonical_hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


@dataclass
class CompositionResult:
    safe: bool
    score: float
    conflicts: List[str] = field(default_factory=list)
    witness: Optional[dict] = None
    provenance: List[str] = field(default_factory=list)


class ConstraintLattice:
    def __init__(self):
        self.hierarchy = {
            ConstraintType.SAFETY: 0.0,
            ConstraintType.OPERATIONAL: 0.3,
            ConstraintType.EPISTEMIC: 0.5,
            ConstraintType.PRUDENTIAL: 0.7,
            ConstraintType.ETHICAL: 1.0,
        }

    def meet(self, c1: Constraint, c2: Constraint) -> Constraint:
        new_strength = max(c1.strength, c2.strength)
        t1 = self.hierarchy[c1.type]
        t2 = self.hierarchy[c2.type]
        new_type = c1.type if t1 >= t2 else c2.type
        new_expr = f"({c1.expression}) AND ({c2.expression})"
        new_domain = c1.domain if c1.domain == c2.domain else "composite"
        cid = canonical_hash({"meet": [c1.as_json(), c2.as_json()]})
        if new_type not in self.hierarchy:
            raise ValueError(f"Unknown constraint type during meet: {new_type}")
        if not 0.0 <= new_strength <= 1.0:
            raise ValueError(f"Constraint strength out of bounds: {new_strength}")
        return Constraint(
            id=cid,
            type=new_type,
            expression=new_expr,
            strength=new_strength,
            domain=new_domain,
            proof_obligation=c1.proof_obligation or c2.proof_obligation,
        )

    def join(self, c1: Constraint, c2: Constraint) -> Constraint:
        new_strength = min(c1.strength, c2.strength)
        t1 = self.hierarchy[c1.type]
        t2 = self.hierarchy[c2.type]
        new_type = c1.type if t1 <= t2 else c2.type
        new_expr = f"({c1.expression}) OR ({c2.expression})"
        new_domain = c1.domain if c1.domain == c2.domain else "composite"
        cid = canonical_hash({"join": [c1.as_json(), c2.as_json()]})
        if new_type not in self.hierarchy:
            raise ValueError(f"Unknown constraint type during join: {new_type}")
        if not 0.0 <= new_strength <= 1.0:
            raise ValueError(f"Constraint strength out of bounds: {new_strength}")
        return Constraint(
            id=cid,
            type=new_type,
            expression=new_expr,
            strength=new_strength,
            domain=new_domain,
            proof_obligation=c1.proof_obligation and c2.proof_obligation,
        )

    def is_composable(self, cs: Set[Constraint]) -> Tuple[bool, CompositionResult]:
        conflicts = []
        provenance = [c.id for c in cs]
        score_accum = sum(c.strength for c in cs) / max(1, len(cs))
        for a in cs:
            for b in cs:
                if a == b:
                    continue
                conflict = check_conflict(a.domain, b.domain)
                if conflict:
                    conflicts.append(f"Domain conflict {a.domain} vs {b.domain}: {conflict}")
                    continue
                if a.expression.strip().lower() == f"not ({b.expression.strip().lower()})":
                    conflicts.append(f"Direct contradiction between {a.id} and {b.id}")
                if (
                    a.type == ConstraintType.SAFETY
                    and b.type == ConstraintType.OPERATIONAL
                    and a.strength >= 0.8
                    and b.strength >= 0.8
                ):
                    conflicts.append(f"Safety({a.id}) vs Operational({b.id}) high-strength conflict")
                if (
                    a.type == ConstraintType.ETHICAL
                    and b.type == ConstraintType.OPERATIONAL
                    and a.strength >= 0.9
                    and "(optimize" in b.expression.lower()
                ):
                    conflicts.append(f"Ethical({a.id}) vs Operational optimization {b.id}")
        if conflicts:
            return False, CompositionResult(
                safe=False,
                score=score_accum,
                conflicts=conflicts,
                witness=None,
                provenance=provenance,
            )
        return True, CompositionResult(safe=True, score=score_accum, provenance=provenance)


__all__ = [
    "parse",
    "meet",
    "is_composable",
    "verify",
    "ConstraintType",
    "Constraint",
    "ConstraintLattice",
]

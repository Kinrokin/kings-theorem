from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Tuple, List, Dict, Optional
import hashlib, json

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
    expression: str            # A canonical string / small AST or SMT expression
    strength: float            # 0.0..1.0 (higher = stronger)
    domain: str
    proof_obligation: bool = False

    def as_json(self):
        return {
            "id": self.id,
            "type": self.type.value,
            "expression": self.expression,
            "strength": self.strength,
            "domain": self.domain,
            "proof_obligation": self.proof_obligation
        }

def canonical_hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

@dataclass
class CompositionResult:
    safe: bool
    score: float
    conflicts: List[str] = field(default_factory=list)
    witness: Optional[dict] = None    # optional counterexample
    provenance: List[str] = field(default_factory=list)

class ConstraintLattice:
    def __init__(self):
        # dominance numeric value for types (higher means more dominant)
        self.hierarchy = {
            ConstraintType.SAFETY: 0.0,
            ConstraintType.OPERATIONAL: 0.3,
            ConstraintType.EPISTEMIC: 0.5,
            ConstraintType.PRUDENTIAL: 0.7,
            ConstraintType.ETHICAL: 1.0
        }

    def meet(self, c1: Constraint, c2: Constraint) -> Constraint:
        new_strength = max(c1.strength, c2.strength)
        t1 = self.hierarchy[c1.type]
        t2 = self.hierarchy[c2.type]
        new_type = c1.type if t1 >= t2 else c2.type
        new_expr = f"({c1.expression}) AND ({c2.expression})"
        new_domain = c1.domain if c1.domain == c2.domain else "composite"
        cid = canonical_hash({"meet": [c1.as_json(), c2.as_json()]})
        return Constraint(id=cid, type=new_type, expression=new_expr,
                          strength=new_strength, domain=new_domain,
                          proof_obligation=c1.proof_obligation or c2.proof_obligation)

    def join(self, c1: Constraint, c2: Constraint) -> Constraint:
        new_strength = min(c1.strength, c2.strength)
        t1 = self.hierarchy[c1.type]
        t2 = self.hierarchy[c2.type]
        new_type = c1.type if t1 <= t2 else c2.type
        new_expr = f"({c1.expression}) OR ({c2.expression})"
        new_domain = c1.domain if c1.domain == c2.domain else "composite"
        cid = canonical_hash({"join": [c1.as_json(), c2.as_json()]})
        return Constraint(id=cid, type=new_type, expression=new_expr,
                          strength=new_strength, domain=new_domain,
                          proof_obligation=c1.proof_obligation and c2.proof_obligation)

    def is_composable(self, cs: Set[Constraint]) -> Tuple[bool, CompositionResult]:
        """
        Conservative composition check. Returns CompositionResult with
        conflicts if any incompatibilities found.
        """
        # Quick trivial checks: duplicate contradictory domain-level rules
        # 1) If any pair has direct syntactic contradiction (expr == NOT other.expr), mark conflict.
        conflicts = []
        provenance = [c.id for c in cs]
        score_accum = sum(c.strength for c in cs) / max(1, len(cs))

        # Pairwise conflict heuristics (extendable): contradictory types with high strength
        for a in cs:
            for b in cs:
                if a == b:
                    continue
                # Exact contradiction heuristic
                if a.expression.strip().lower() == f"not ({b.expression.strip().lower()})":
                    conflicts.append(f"Direct contradiction between {a.id} and {b.id}")
                # Safety vs. high-risk operational conflict: if safety strong and op strong -> conflict
                if a.type == ConstraintType.SAFETY and b.type == ConstraintType.OPERATIONAL:
                    if a.strength >= 0.8 and b.strength >= 0.8:
                        conflicts.append(f"Safety({a.id}) vs Operational({b.id}) high-strength conflict")
                # Ethical vs. pragmatic: if ethics strong and op contradictory expression substring
                if a.type == ConstraintType.ETHICAL and b.type == ConstraintType.OPERATIONAL:
                    if a.strength >= 0.9 and "(optimize" in b.expression.lower():
                        conflicts.append(f"Ethical({a.id}) likely conflicts with Operational optimization {b.id}")
        if conflicts:
            return False, CompositionResult(safe=False, score=score_accum, conflicts=conflicts, witness=None, provenance=provenance)
        # else return safe
        return True, CompositionResult(safe=True, score=score_accum, provenance=provenance)

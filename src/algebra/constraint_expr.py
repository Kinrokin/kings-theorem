# src/algebra/constraint_expr.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Union, List, Set, Dict, Any
import json

# Basic AST nodes
@dataclass(frozen=True)
class Atom:
    name: str  # e.g., "NO_EXFIL", "NO_PERSONAL_DATA", "DOMAIN:HEALTH"

    def serialize(self) -> Dict[str, Any]:
        return {"atom": self.name}

    def __str__(self):
        return self.name

@dataclass(frozen=True)
class And:
    parts: tuple

    def serialize(self) -> Dict[str, Any]:
        return {"and": [p.serialize() for p in self.parts]}

    def __str__(self):
        return " AND ".join(str(p) for p in self.parts)

@dataclass(frozen=True)
class Or:
    parts: tuple

    def serialize(self) -> Dict[str, Any]:
        return {"or": [p.serialize() for p in self.parts]}

    def __str__(self):
        return " OR ".join(str(p) for p in self.parts)

@dataclass(frozen=True)
class Not:
    part: object

    def serialize(self) -> Dict[str, Any]:
        return {"not": self.part.serialize()}

    def __str__(self):
        return f"NOT({self.part})"

ConstraintExpr = Union[Atom, And, Or, Not]

def canonical_serialize(expr: ConstraintExpr) -> str:
    """
    Deterministic JSON serialization for AST -> string.
    """
    return json.dumps(expr.serialize(), sort_keys=True, separators=(",", ":"))

def atoms_in(expr: ConstraintExpr) -> Set[str]:
    if isinstance(expr, Atom):
        return {expr.name}
    if isinstance(expr, Not):
        return atoms_in(expr.part)
    if isinstance(expr, And) or isinstance(expr, Or):
        s = set()
        for p in expr.parts:
            s.update(atoms_in(p))
        return s
    return set()

def simple_conflict_check(exprs: List[ConstraintExpr]) -> tuple[bool, str]:
    """
    Very simple conflict detection:
      - If both A and NOT A appear -> conflict.
      - If explicit contradictory atoms found (like DOMAIN:HEALTH vs DOMAIN:FINANCE) -> conflict.
    This is intentionally conservative and designed to catch obvious contradictions early.
    """
    atoms = set()
    negs = set()
    for e in exprs:
        if isinstance(e, Atom):
            atoms.add(e.name)
        elif isinstance(e, Not):
            inner = e.part
            if isinstance(inner, Atom):
                negs.add(inner.name)
        else:
            atoms.update(atoms_in(e))
    # direct contradiction
    inter = atoms.intersection(negs)
    if inter:
        return False, f"direct_contradiction:{','.join(sorted(inter))}"
    # domain conflicts heuristic
    domains = {a.split(":",1)[0] for a in atoms if ":" in a}
    if len(domains) > 1 and "DOMAIN" in domains:
        # crude detection; real logic should inspect domains properly
        return False, f"domain_conflict:{','.join(sorted(domains))}"
    return True, "ok"

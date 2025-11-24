# src/proofs/proof_lang.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Dict, List, Optional
import uuid
import logging

logger = logging.getLogger("kt.proofs")
logger.setLevel(logging.INFO)


class ProofStatus(Enum):
    PROVEN = "PROVEN"
    REFUTED = "REFUTED"
    PENDING = "PENDING"
    CONTRADICTORY = "CONTRADICTORY"


@dataclass(frozen=True)
class ConstraintRef:
    id: str
    expression: str


@dataclass
class ProofStep:
    step_id: str
    rule: str  # name of rule used, e.g., "AND_INTRO", "AND_ELIM", "ASSUME"
    premises: List[str]  # step_ids
    conclusion: str  # proposition text


@dataclass
class ProofObject:
    proof_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposition: str = ""
    assumptions: Set[str] = field(default_factory=set)  # assumption ids or texts
    steps: List[ProofStep] = field(default_factory=list)
    required_invariants: Set[ConstraintRef] = field(default_factory=set)
    claimed_satisfactions: Dict[str, bool] = field(default_factory=dict)  # constraint_id -> bool
    status: ProofStatus = ProofStatus.PENDING


class ProofChecker:
    """
    Minimal structural proof checker:
      - verifies all premise step_ids exist
      - detects cycles in derivation graph
      - verifies that claimed satisfactions map to actual checks (requires external constraint verifier)
    """

    def __init__(self, constraint_verifier=None):
        # constraint_verifier: callable(constraint_ref)->bool
        self.constraint_verifier = constraint_verifier

    def check_proof(self, proof: ProofObject) -> ProofStatus:
        # structural checks
        step_map = {s.step_id: s for s in proof.steps}
        # 1) verify premises exist
        for s in proof.steps:
            for pid in s.premises:
                if pid not in step_map and pid not in proof.assumptions:
                    logger.debug("Missing premise %s in step %s", pid, s.step_id)
                    return ProofStatus.REFUTED
        # 2) detect cycles
        if self._has_cycle(step_map):
            logger.debug("Cycle detected in proof %s", proof.proof_id)
            return ProofStatus.CONTRADICTORY
        # 3) check claimed invariants
        for cref in proof.required_invariants:
            valid = True
            if self.constraint_verifier:
                valid = bool(self.constraint_verifier(cref))
            claimed = proof.claimed_satisfactions.get(cref.id, False)
            if claimed and not valid:
                return ProofStatus.REFUTED
            if not claimed:
                return ProofStatus.PENDING
        # If we get here, mark PROVEN
        return ProofStatus.PROVEN

    def _has_cycle(self, step_map: Dict[str, ProofStep]) -> bool:
        visiting = set()
        visited = set()

        def dfs(u):
            if u in visiting:
                return True
            if u in visited:
                return False
            visiting.add(u)
            for v in step_map[u].premises:
                if v in step_map and dfs(v):
                    return True
            visiting.remove(u)
            visited.add(u)
            return False

        for s in step_map:
            if dfs(s):
                return True
        return False

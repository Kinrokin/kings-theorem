# src/proofs/proof_lang.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Set, Dict, List, Optional
import uuid
import logging
from src.metrics.metrics import record_proof_check

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
    Enhanced structural proof checker with meta-checks:
      - verifies all premise step_ids exist
      - detects cycles in derivation graph
      - detects self-endorsement (proof citing itself as premise)
      - enforces proof depth limits (prevents infinitely deep proofs)
      - verifies that claimed satisfactions map to actual checks (requires external constraint verifier)
    """

    def __init__(self, constraint_verifier=None, max_proof_depth: int = 20, allow_self_reference: bool = False):
        # constraint_verifier: callable(constraint_ref)->bool
        self.constraint_verifier = constraint_verifier
        self.max_proof_depth = max_proof_depth
        self.allow_self_reference = allow_self_reference

    def check_proof(self, proof: ProofObject) -> ProofStatus:
        # structural checks
        step_map = {s.step_id: s for s in proof.steps}
        
        # 1) verify premises exist
        for s in proof.steps:
            for pid in s.premises:
                if pid not in step_map and pid not in proof.assumptions:
                    logger.debug("Missing premise %s in step %s", pid, s.step_id)
                    try:
                        record_proof_check(False)
                    except Exception:
                        pass
                    return ProofStatus.REFUTED
        
        # 2) detect cycles
        if self._has_cycle(step_map):
            logger.debug("Cycle detected in proof %s", proof.proof_id)
            try:
                record_proof_check(False)
            except Exception:
                pass
            return ProofStatus.CONTRADICTORY
        
        # 3) detect self-endorsement (proof citing its own conclusion)
        if not self.allow_self_reference:
            if self._has_self_endorsement(proof, step_map):
                logger.debug("Self-endorsement detected in proof %s", proof.proof_id)
                try:
                    record_proof_check(False)
                except Exception:
                    pass
                return ProofStatus.CONTRADICTORY
        
        # 4) enforce proof depth limits
        max_depth = self._compute_max_depth(step_map)
        if max_depth > self.max_proof_depth:
            logger.debug("Proof depth %d exceeds limit %d", max_depth, self.max_proof_depth)
            try:
                record_proof_check(False)
            except Exception:
                pass
            return ProofStatus.REFUTED
        
        # 5) check claimed invariants
        for cref in proof.required_invariants:
            valid = True
            if self.constraint_verifier:
                valid = bool(self.constraint_verifier(cref))
            claimed = proof.claimed_satisfactions.get(cref.id, False)
            if claimed and not valid:
                logger.debug("Claimed invariant %s not satisfied", cref.id)
                try:
                    record_proof_check(False)
                except Exception:
                    pass
                return ProofStatus.REFUTED
            if not claimed:
                # pending does not count as success/failure
                return ProofStatus.PENDING
        
        # If we get here, mark PROVEN
        try:
            record_proof_check(True)
        except Exception:
            pass
        return ProofStatus.PROVEN

    def _has_cycle(self, step_map: Dict[str, ProofStep]) -> bool:
        """Detect cycles in proof derivation graph using DFS."""
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
    
    def _has_self_endorsement(self, proof: ProofObject, step_map: Dict[str, ProofStep]) -> bool:
        """
        Detect self-endorsement: a proof step that cites the proof's main proposition
        as a premise without deriving it from assumptions.
        """
        # Check if any step's conclusion matches the main proposition and is used as premise
        for step in proof.steps:
            if step.conclusion == proof.proposition:
                # This step claims to prove the main proposition
                # Check if it's used as a premise elsewhere
                for other_step in proof.steps:
                    if step.step_id in other_step.premises and other_step.step_id != step.step_id:
                        # Check if the step has proper derivation (non-trivial premises)
                        if not step.premises or all(p == step.step_id for p in step.premises):
                            logger.debug(f"Self-endorsement: step {step.step_id} claims '{proof.proposition}' without proper derivation")
                            return True
        return False
    
    def _compute_max_depth(self, step_map: Dict[str, ProofStep]) -> int:
        """
        Compute maximum depth of proof derivation tree.
        Depth = longest path from any leaf (no premises) to any step.
        """
        memo = {}
        
        def depth(step_id: str) -> int:
            if step_id in memo:
                return memo[step_id]
            if step_id not in step_map:
                return 0  # Assumption (leaf)
            
            step = step_map[step_id]
            if not step.premises:
                memo[step_id] = 1
                return 1
            
            max_premise_depth = max((depth(p) for p in step.premises), default=0)
            memo[step_id] = max_premise_depth + 1
            return memo[step_id]
        
        if not step_map:
            return 0
        
        return max(depth(sid) for sid in step_map)

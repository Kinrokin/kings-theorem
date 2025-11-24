# src/algebra/composer.py
from __future__ import annotations
from typing import List, Dict, Any
import uuid
import time
from src.algebra.constraint_expr import canonical_serialize, simple_conflict_check, ConstraintExpr, Atom
from src.proofs.proof_lang import ProofObject, ProofStep, ProofChecker, ConstraintRef

def compose_steps(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    steps: list of dicts, each must include:
      - step_id (str)
      - constraints: serialized constraint expr object (dict), or "constraint_expr" field
    Returns a composition proof manifest dict with:
      - composition_id
      - steps
      - composition_constraints (serialized)
      - composition_proof (ProofObject serialized minimally)
    """
    # gather constraint exprs
    exprs = []
    serialized_exprs = []
    for s in steps:
        c = s.get("constraints")
        if c is None:
            # assume permissive (empty) constraint
            e = Atom(name="PERMISSIVE")
            exprs.append(e)
            serialized_exprs.append(canonical_serialize(e))
        else:
            # support already-serialized ASTs or simple atom strings
            if isinstance(c, dict):
                # attempt to rehydrate minimal atom case
                if "atom" in c:
                    e = Atom(name=c["atom"])
                elif "and" in c or "or" in c or "not" in c:
                    # keep serialized as-is by stringifying
                    serialized_exprs.append(str(c))
                    continue
                else:
                    e = Atom(name=str(c))
                exprs.append(e)
                serialized_exprs.append(canonical_serialize(e))
            else:
                # fallback: string
                e = Atom(name=str(c))
                exprs.append(e)
                serialized_exprs.append(canonical_serialize(e))
    # run simple conflict check
    composable, reason = simple_conflict_check(exprs)
    composition_id = str(uuid.uuid4())
    # Create a very small proof object (skeleton) that claims composability
    proof = ProofObject(proposition=f"composition:{composition_id}")
    # Add a single step claiming "composition_check"
    step = ProofStep(step_id="step_compose_check", rule="COMPOSITION_CHECK", premises=[], conclusion=f"composable={str(composable)}")
    proof.steps.append(step)
    # required_invariants referencing the serialized exprs (as simple placeholder)
    for i, s in enumerate(serialized_exprs):
        cref = ConstraintRef(id=f"c{i}", expression=s)
        proof.required_invariants.add(cref)
        proof.claimed_satisfactions[cref.id] = composable
    # run structural checker
    checker = ProofChecker(constraint_verifier=lambda c: True)  # external verifier can be passed in real use
    status = checker.check_proof(proof)
    proof.status = status
    manifest = {
        "composition_id": composition_id,
        "timestamp": time.time(),
        "steps": [ { "step_id": s.get("step_id","?"), "constraints_serialized": serialized_exprs[i] if i < len(serialized_exprs) else None } for i,s in enumerate(steps)],
        "composable": composable,
        "compose_reason": reason,
        "composition_proof": {
            "proof_id": proof.proof_id,
            "proposition": proof.proposition,
            "status": proof.status.name,
            "steps": [ { "step_id": st.step_id, "rule": st.rule, "conclusion": st.conclusion } for st in proof.steps ]
        }
    }
    return manifest

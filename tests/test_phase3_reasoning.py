import pytest

from src.algebra.constraint_lattice import Constraint, ConstraintLattice, ConstraintType
from src.reasoning.counterfactual_engine import CounterfactualEngine
from src.reasoning.proof_system import ProofChecker, ProofObject, ProofStatus


def test_counterfactual_fatal_on_axiomatic_contradiction():
    L = ConstraintLattice()
    # create contradictory constraints: a == not (b)
    a = Constraint(id="a", type=ConstraintType.SAFETY, expression="x > 0", strength=0.9, domain="d")
    b = Constraint(id="b", type=ConstraintType.OPERATIONAL, expression="not (x > 0)", strength=0.8, domain="d")
    engine = CounterfactualEngine(L)
    world = engine._evaluate_composition_path(["A", "B"], {a, b})
    assert world.violation_potential == 1.0
    assert any("FATAL" in s for s in world.path_trace)


def test_counterfactual_heuristic_risk():
    L = ConstraintLattice()
    c = Constraint(id="c", type=ConstraintType.OPERATIONAL, expression="(optimize x)", strength=0.4, domain="d")
    engine = CounterfactualEngine(L)
    # path length 3, last element indicates RISK_ACTION, no safety constraint
    world = engine._evaluate_composition_path(["step1", "step2", "RISK_ACTION_xyz"], {c})
    assert world.violation_potential == 0.75
    assert any("High-risk" in s for s in world.path_trace)


def test_proofchecker_refute_and_contradict():
    checker = ProofChecker()
    # REFUTED case
    p1 = ProofObject(proof_id="p1", claims={"NoIrreversibleHarm": False})
    status1 = checker.check_proof(p1, required_invariants=["NoIrreversibleHarm"])
    assert status1 == ProofStatus.REFUTED

    # CONTRADICTORY case
    p2 = ProofObject(proof_id="p2", claims={"x": True, "not (x)": True})
    status2 = checker.check_proof(p2)
    assert status2 == ProofStatus.CONTRADICTORY

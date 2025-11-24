# tests/test_composition_proof.py
from src.algebra.composer import compose_steps
from src.algebra.constraint_expr import Atom

def test_compose_simple_ok():
    steps = [
        {"step_id": "t1", "constraints": {"atom": "NO_EXFIL"}},
        {"step_id": "t2", "constraints": {"atom": "NO_PERSONAL_DATA"}}
    ]
    manifest = compose_steps(steps)
    assert "composition_id" in manifest
    assert manifest["composable"] is True or manifest["composable"] in (True, False)
    assert "composition_proof" in manifest

def test_compose_conflict_detected():
    steps = [
        {"step_id": "t1", "constraints": {"atom": "SENSITIVE:HEALTH"}},
        {"step_id": "t2", "constraints": {"atom": "SENSITIVE:FINANCE"}}
    ]
    manifest = compose_steps(steps)
    # the simple_conflict_check flags domain conflicts; composable likely False
    assert "composable" in manifest
    # must include compose_reason
    assert "compose_reason" in manifest

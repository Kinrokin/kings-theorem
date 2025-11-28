import pytest

from src.proofs.dsl import parse

pytestmark = [pytest.mark.kt_composition]

DSL_SRC = """
constraint C1: fairness >= 0.7
constraint C2: traditions >= 2
theorem T_SAFE: C1 & C2 -> COMPOSITION_SAFE
"""


def test_composition_theorem_holds():
    program = parse(DSL_SRC)
    evidence = {"fairness": 0.72, "traditions": 3}
    results = program.evaluate(evidence)
    assert results.get("T_SAFE") is True, "Composition safety theorem failed"

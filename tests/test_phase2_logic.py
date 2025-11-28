from src.algebra.constraint_lattice import Constraint, ConstraintLattice, ConstraintType
from src.ethics.manifold import EthicalManifold, ManifoldProjector


def test_meet_join_basic():
    a = Constraint(
        id="a",
        type=ConstraintType.SAFETY,
        expression="x>0",
        strength=0.9,
        domain="math",
    )
    b = Constraint(
        id="b",
        type=ConstraintType.EPISTEMIC,
        expression="prov(x)",
        strength=0.8,
        domain="math",
    )
    L = ConstraintLattice()
    m = L.meet(a, b)
    j = L.join(a, b)
    assert m.strength == max(a.strength, b.strength)
    assert j.strength == min(a.strength, b.strength)


def test_composable_simple():
    a = Constraint(
        id="a",
        type=ConstraintType.SAFETY,
        expression="x>0",
        strength=0.9,
        domain="math",
    )
    b = Constraint(
        id="b",
        type=ConstraintType.OPERATIONAL,
        expression="(optimize x)",
        strength=0.4,
        domain="math",
    )
    L = ConstraintLattice()
    ok, res = L.is_composable({a, b})
    assert ok is True


def test_manifold_projection_clamp():
    manifold = EthicalManifold(dimensions={"fairness": (0.0, 1.0), "non_maleficence": (0.0, 1.0)})
    proj = ManifoldProjector(manifold)
    input_vec = {"fairness": 1.2, "non_maleficence": -0.5}
    p, ok = proj.project(input_vec)
    assert ok is False
    assert 0.0 <= p["non_maleficence"] <= 1.0

"""
Test ethical manifold convex projection and corner attack scenarios.
"""


def test_manifold_corner_attack():
    """Test that adversarial corner values are properly projected into manifold."""
    from src.ethics.manifold import EthicalManifold, project

    manifold = EthicalManifold.from_bounds({"fairness": (0, 1), "beneficence": (0, 1), "non_maleficence": (0, 1)})

    # Craft adversarial point that axis-clamping would hide:
    # huge fairness, negative non-maleficence
    x = {"fairness": 1000.0, "beneficence": 0.5, "non_maleficence": -1000.0}
    projected, is_safe = project(manifold, x)

    # Must project into valid range
    assert manifold.contains(projected)
    assert not is_safe  # Should flag as unsafe


def test_manifold_contains_safe_point():
    """Test that safe points are recognized."""
    from src.ethics.manifold import EthicalManifold

    manifold = EthicalManifold.from_bounds({"fairness": (0, 1), "beneficence": (0, 1)})

    safe_point = {"fairness": 0.5, "beneficence": 0.7}
    assert manifold.contains(safe_point)


def test_manifold_projection_distance():
    """Test that projection minimizes distance."""
    from src.ethics.manifold import EthicalManifold, project

    manifold = EthicalManifold.from_bounds({"fairness": (0, 1), "beneficence": (0, 1)})

    # Point just outside bounds
    x = {"fairness": 1.2, "beneficence": 0.5}
    projected, is_safe = project(manifold, x)

    # Should clamp fairness to 1.0
    assert abs(projected["fairness"] - 1.0) < 0.01
    assert abs(projected["beneficence"] - 0.5) < 0.01
    assert not is_safe


def test_manifold_multi_violation():
    """Test projection with multiple dimensions violating bounds."""
    from src.ethics.manifold import EthicalManifold, project

    manifold = EthicalManifold.from_bounds({"fairness": (0, 1), "beneficence": (0, 1), "non_maleficence": (0, 1)})

    # All dimensions out of bounds
    x = {"fairness": -0.5, "beneficence": 1.5, "non_maleficence": 2.0}
    projected, is_safe = project(manifold, x)

    # All should be clamped to valid ranges
    assert manifold.contains(projected)
    assert not is_safe


def test_manifold_edge_case_zero():
    """Test projection at boundary values."""
    from src.ethics.manifold import EthicalManifold, project

    manifold = EthicalManifold.from_bounds({"fairness": (0, 1), "beneficence": (0, 1)})

    # Point at lower bound
    x = {"fairness": 0.0, "beneficence": 0.0}
    projected, is_safe = project(manifold, x)

    assert manifold.contains(projected)
    assert is_safe  # Within bounds

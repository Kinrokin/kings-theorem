"""
Test counterfactual engine probabilistic discovery of adversarial paths.
"""
import pytest


class DummyKernel:
    """Simple kernel for testing."""
    def __init__(self, name: str, val: float):
        self.name = name
        self.val = val

    def process(self, input_data):
        return {"x": self.val, "name": self.name}


def test_counterfactual_discovery():
    """Test that counterfactual engine discovers adversarial kernel combinations."""
    from src.reasoning.counterfactual_engine import CounterfactualEngine

    # Registry with one adversarial kernel (huge negative value)
    kr = {
        "k1": DummyKernel("k1", 0.1),
        "k2": DummyKernel("k2", -1e9),  # Adversarial
        "k3": DummyKernel("k3", 0.2)
    }
    engine = CounterfactualEngine(kernel_registry=kr, rng_seed=123)
    worlds = engine.explore_composition_space(input_data={}, monte_carlo_samples=500)

    # Should find high-violation paths (lower threshold since we only have 3 kernels)
    bad = engine.find_violation_paths(worlds, threshold=0.15)
    assert len(bad) > 0, f"Should discover adversarial paths. Found {len(worlds)} worlds, {len(bad)} violations"


def test_counterfactual_safe_composition():
    """Test that safe kernel compositions are recognized."""
    from src.reasoning.counterfactual_engine import CounterfactualEngine

    # All safe kernels
    kr = {
        "k1": DummyKernel("k1", 0.5),
        "k2": DummyKernel("k2", 0.6),
        "k3": DummyKernel("k3", 0.7)
    }
    engine = CounterfactualEngine(kernel_registry=kr, rng_seed=42)
    worlds = engine.explore_composition_space(input_data={}, monte_carlo_samples=100)

    # Should have low violation scores
    bad = engine.find_violation_paths(worlds, threshold=0.5)
    assert len(bad) == 0, "Safe kernels should not trigger violations"


def test_counterfactual_dependency_graph():
    """Test dependency-aware exploration."""
    from src.reasoning.counterfactual_engine import CounterfactualEngine

    kr = {
        "k1": DummyKernel("k1", 0.1),
        "k2": DummyKernel("k2", 0.2),
        "k3": DummyKernel("k3", 0.3),
        "k4": DummyKernel("k4", 0.4)
    }
    engine = CounterfactualEngine(kernel_registry=kr, rng_seed=99)

    # Add dependencies
    engine.add_dependency("k1", "k2")
    engine.add_dependency("k3", "k4")

    # Should identify connected components
    comps = engine.deps.connected_components()
    assert len(comps) == 2, "Should find 2 connected components"


def test_counterfactual_nan_detection():
    """Test detection of NaN/Inf outputs."""
    from src.reasoning.counterfactual_engine import CounterfactualEngine
    import numpy as np

    class BadKernel:
        def __init__(self, name):
            self.name = name
        def process(self, _):
            return {"x": float('nan'), "name": self.name}

    kr = {
        "k1": DummyKernel("k1", 0.5),
        "k2": BadKernel("k2_bad")
    }
    engine = CounterfactualEngine(kernel_registry=kr, rng_seed=55)
    worlds = engine.explore_composition_space(input_data={}, monte_carlo_samples=50)

    # Should detect NaN as violation
    bad = engine.find_violation_paths(worlds, threshold=0.2)
    assert len(bad) > 0, "Should detect NaN violations"

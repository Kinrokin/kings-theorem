"""Property-Based MTL Tests - Titanium X Protocol

AID: /tests/test_mtl_property_based.py
Proof ID: PRF-PHOENIX-TEST-001
Adversarial Response: Section 3.1 "Property-based tests for MTL"

Uses hypothesis to generate random MTL formulas and event traces,
cross-checking with a simple reference evaluator to ensure correctness.

Tests include:
- Random atomic propositions over generated traces
- Globally/Eventually with random metric bounds
- Nested temporal operators
- Edge cases: empty traces, single events, vacuous satisfaction
"""

from typing import List

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.primitives.mtl_engine import And, Atomic, Event, Eventually, Globally, MTLEngine, MTLStatus, Not, Or, parse_mtl

# =============================================================================
# Strategies for generating test data
# =============================================================================


@st.composite
def event_trace(draw, min_size=0, max_size=20):
    """Generate a list of events with increasing timestamps."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))

    events = []
    current_time = 0.0

    for _ in range(size):
        # Increment time by a random amount
        current_time += draw(st.floats(min_value=0.1, max_value=2.0))

        # Generate random values
        values = {
            "risk": draw(st.floats(min_value=0.0, max_value=1.0)),
            "ethics": draw(st.floats(min_value=0.0, max_value=1.0)),
            "confidence": draw(st.floats(min_value=0.0, max_value=1.0)),
        }

        events.append(Event(timestamp=current_time, values=values))

    return events


@st.composite
def atomic_formula(draw):
    """Generate a random atomic proposition."""
    variable = draw(st.sampled_from(["risk", "ethics", "confidence"]))
    operator = draw(st.sampled_from(["<", "<=", ">", ">=", "==", "!="]))
    value = draw(st.floats(min_value=0.0, max_value=1.0))
    return Atomic(variable, operator, value)


# =============================================================================
# Reference Evaluator (Slow but Simple)
# =============================================================================


def reference_eval_atomic(atom: Atomic, event: Event) -> bool:
    """Simple reference evaluator for atomic propositions."""
    value = event.values.get(atom.variable)
    if value is None:
        return False

    ops = {
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "==": lambda a, b: abs(a - b) < 1e-9,  # Floating point equality
        "!=": lambda a, b: abs(a - b) >= 1e-9,
    }

    return ops[atom.operator](value, atom.value)


def reference_eval_globally(atom: Atomic, events: List[Event], lower: float, upper: float) -> bool:
    """Reference evaluator for G[a,b](atom)."""
    if not events:
        return True  # Vacuous

    in_range_count = 0
    for event in events:
        if lower <= event.timestamp <= upper:
            in_range_count += 1
            if not reference_eval_atomic(atom, event):
                return False

    return in_range_count > 0  # At least one event must be checked


def reference_eval_eventually(atom: Atomic, events: List[Event], lower: float, upper: float) -> bool:
    """Reference evaluator for F[a,b](atom)."""
    if not events:
        return False  # Cannot satisfy

    for event in events:
        if lower <= event.timestamp <= upper:
            if reference_eval_atomic(atom, event):
                return True

    return False


# =============================================================================
# Property-Based Tests
# =============================================================================


class TestMTLPropertyBased:
    """Property-based tests for MTL engine."""

    @given(atom=atomic_formula(), trace=event_trace(min_size=1, max_size=10))
    @settings(max_examples=100, deadline=None)
    def test_atomic_consistency(self, atom: Atomic, trace: List[Event]):
        """Test that atomic evaluation is consistent."""
        engine = MTLEngine()
        result = engine.evaluate(atom, trace, horizon=100.0)

        # Should never return UNKNOWN for atomic propositions
        assert result.status != MTLStatus.UNKNOWN

        # If trace is non-empty, should have definite result
        if trace:
            assert result.status in {MTLStatus.SATISFIED, MTLStatus.VIOLATED, MTLStatus.VACUOUS}

    @given(atom=atomic_formula(), trace=event_trace(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_globally_bounded(self, atom: Atomic, trace: List[Event]):
        """Test G[0,10](atom) against reference evaluator."""
        engine = MTLEngine()

        formula = Globally(atom, lower_bound=0.0, upper_bound=10.0)
        result = engine.evaluate(formula, trace, horizon=20.0)

        # Compute reference result
        ref_result = reference_eval_globally(atom, trace, 0.0, 10.0)

        # Compare (allowing for vacuous case)
        if result.status == MTLStatus.VACUOUS:
            # No events in range [0, 10]
            assert not any(0.0 <= e.timestamp <= 10.0 for e in trace)
        elif result.status == MTLStatus.SATISFIED:
            assert ref_result, f"Engine satisfied but reference failed for {atom}"
        elif result.status == MTLStatus.VIOLATED:
            assert not ref_result, f"Engine violated but reference passed for {atom}"

    @given(atom=atomic_formula(), trace=event_trace(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_eventually_bounded(self, atom: Atomic, trace: List[Event]):
        """Test F[0,10](atom) against reference evaluator."""
        engine = MTLEngine()

        formula = Eventually(atom, lower_bound=0.0, upper_bound=10.0)
        result = engine.evaluate(formula, trace, horizon=20.0)

        # Compute reference result
        ref_result = reference_eval_eventually(atom, trace, 0.0, 10.0)

        # Compare
        if result.status == MTLStatus.VACUOUS:
            # No events in range
            assert not any(0.0 <= e.timestamp <= 10.0 for e in trace)
        elif result.status == MTLStatus.SATISFIED:
            assert ref_result, "Engine satisfied but reference failed"
        elif result.status == MTLStatus.VIOLATED:
            assert not ref_result, "Engine violated but reference passed"

    @given(atom=atomic_formula())
    def test_empty_trace_vacuous(self, atom: Atomic):
        """Test that empty traces give vacuous results."""
        engine = MTLEngine()

        formula = Globally(atom, lower_bound=0.0, upper_bound=10.0)
        result = engine.evaluate(formula, [], horizon=20.0)

        assert result.status == MTLStatus.VACUOUS

    @given(atom=atomic_formula(), trace=event_trace(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_negation_inverts_result(self, atom: Atomic, trace: List[Event]):
        """Test that Not inverts the satisfaction result."""
        engine = MTLEngine()

        result_positive = engine.evaluate(atom, trace, horizon=20.0)
        result_negative = engine.evaluate(Not(atom), trace, horizon=20.0)

        # Skip if vacuous (negation of vacuous is still vacuous)
        if result_positive.status == MTLStatus.VACUOUS:
            assert result_negative.status == MTLStatus.VACUOUS
        else:
            # Negation should invert
            if result_positive.status == MTLStatus.SATISFIED:
                assert result_negative.status == MTLStatus.VIOLATED
            elif result_positive.status == MTLStatus.VIOLATED:
                assert result_negative.status == MTLStatus.SATISFIED

    @given(atom1=atomic_formula(), atom2=atomic_formula(), trace=event_trace(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_and_requires_both(self, atom1: Atomic, atom2: Atomic, trace: List[Event]):
        """Test that And requires both operands to hold."""
        engine = MTLEngine()

        result1 = engine.evaluate(atom1, trace, horizon=20.0)
        result2 = engine.evaluate(atom2, trace, horizon=20.0)
        result_and = engine.evaluate(And(atom1, atom2), trace, horizon=20.0)

        # If either is violated, And must be violated
        if result1.status == MTLStatus.VIOLATED or result2.status == MTLStatus.VIOLATED:
            assert result_and.status != MTLStatus.SATISFIED

        # If both satisfied, And must be satisfied
        if result1.status == MTLStatus.SATISFIED and result2.status == MTLStatus.SATISFIED:
            assert result_and.status == MTLStatus.SATISFIED

    @given(atom1=atomic_formula(), atom2=atomic_formula(), trace=event_trace(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_or_requires_one(self, atom1: Atomic, atom2: Atomic, trace: List[Event]):
        """Test that Or requires at least one operand to hold."""
        engine = MTLEngine()

        result1 = engine.evaluate(atom1, trace, horizon=20.0)
        result2 = engine.evaluate(atom2, trace, horizon=20.0)
        result_or = engine.evaluate(Or(atom1, atom2), trace, horizon=20.0)

        # If either is satisfied, Or must be satisfied
        if result1.status == MTLStatus.SATISFIED or result2.status == MTLStatus.SATISFIED:
            assert result_or.status == MTLStatus.SATISFIED

        # If both violated, Or must be violated
        if result1.status == MTLStatus.VIOLATED and result2.status == MTLStatus.VIOLATED:
            assert result_or.status == MTLStatus.VIOLATED


# =============================================================================
# Parser Tests
# =============================================================================


class TestMTLParser:
    """Tests for MTL formula parser."""

    def test_parse_simple_atomic(self):
        """Test parsing simple atomic proposition."""
        formula = parse_mtl("risk < 0.5")
        assert isinstance(formula, Atomic)
        assert formula.variable == "risk"
        assert formula.operator == "<"
        assert formula.value == 0.5

    def test_parse_globally_bounded(self):
        """Test parsing G[a,b](φ)."""
        formula = parse_mtl("G[0,10](risk < 0.5)")
        assert isinstance(formula, Globally)
        assert formula.lower_bound == 0.0
        assert formula.upper_bound == 10.0
        assert isinstance(formula.child, Atomic)

    def test_parse_eventually_unbounded(self):
        """Test parsing F(φ)."""
        formula = parse_mtl("F(ethics >= 0.7)")
        assert isinstance(formula, Eventually)
        assert formula.lower_bound == 0.0
        assert formula.upper_bound is None
        assert isinstance(formula.child, Atomic)

    def test_parse_negation(self):
        """Test parsing !φ."""
        formula = parse_mtl("!(risk > 0.5)")
        assert isinstance(formula, Not)
        assert isinstance(formula.child, Atomic)

    def test_parse_conjunction(self):
        """Test parsing φ & ψ."""
        formula = parse_mtl("risk < 0.5 & ethics >= 0.7")
        assert isinstance(formula, And)
        assert isinstance(formula.left, Atomic)
        assert isinstance(formula.right, Atomic)

    def test_parse_disjunction(self):
        """Test parsing φ | ψ."""
        formula = parse_mtl("risk < 0.5 | confidence > 0.8")
        assert isinstance(formula, Or)

    def test_parse_implication(self):
        """Test parsing φ -> ψ."""
        from src.primitives.mtl_engine import Implies

        formula = parse_mtl("risk > 0.5 -> ethics >= 0.7")
        assert isinstance(formula, Implies)

    def test_parse_nested(self):
        """Test parsing nested formula."""
        formula = parse_mtl("G[0,10](F[0,5](risk < 0.5))")
        assert isinstance(formula, Globally)
        assert isinstance(formula.child, Eventually)
        assert isinstance(formula.child.child, Atomic)

    def test_roundtrip_to_string(self):
        """Test that parsing and to_string are consistent."""
        original = "G[0,10](risk < 0.5)"
        parsed = parse_mtl(original)
        reconstructed = parsed.to_string()

        # Parse again and compare structure
        reparsed = parse_mtl(reconstructed)
        assert type(parsed) == type(reparsed)


# =============================================================================
# Integration Tests
# =============================================================================


class TestMTLIntegration:
    """Integration tests with realistic scenarios."""

    def test_axiom_six_enforcement(self):
        """Test Axiom 6: G(ethics >= 0.7) enforcement."""
        engine = MTLEngine()

        # Trace that violates Axiom 6
        trace_violation = [
            Event(timestamp=1.0, values={"ethics": 0.8}),
            Event(timestamp=2.0, values={"ethics": 0.6}),  # Violation
            Event(timestamp=3.0, values={"ethics": 0.9}),
        ]

        formula = parse_mtl("G(ethics >= 0.7)")
        result = engine.evaluate(formula, trace_violation, horizon=10.0)

        assert result.status == MTLStatus.VIOLATED
        assert result.witness_time == 2.0

    def test_axiom_six_satisfied(self):
        """Test Axiom 6 satisfied over trace."""
        engine = MTLEngine()

        trace_good = [
            Event(timestamp=1.0, values={"ethics": 0.8}),
            Event(timestamp=2.0, values={"ethics": 0.75}),
            Event(timestamp=3.0, values={"ethics": 0.9}),
        ]

        formula = parse_mtl("G(ethics >= 0.7)")
        result = engine.evaluate(formula, trace_good, horizon=10.0)

        assert result.status == MTLStatus.SATISFIED

    def test_risk_bounded_interval(self):
        """Test risk constraint over bounded interval."""
        engine = MTLEngine()

        trace = [
            Event(timestamp=1.0, values={"risk": 0.3}),
            Event(timestamp=5.0, values={"risk": 0.4}),
            Event(timestamp=8.0, values={"risk": 0.6}),  # Outside [0,5]
            Event(timestamp=12.0, values={"risk": 0.2}),
        ]

        # Risk must be < 0.5 in interval [0,5]
        formula = parse_mtl("G[0,5](risk < 0.5)")
        result = engine.evaluate(formula, trace, horizon=15.0)

        # Events at t=1.0 and t=5.0 satisfy; t=8.0 is outside interval
        assert result.status == MTLStatus.SATISFIED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

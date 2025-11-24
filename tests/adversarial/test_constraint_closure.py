"""
Test constraint expression closure properties and validation.
"""
import pytest


def test_constraint_expr_simple_atom():
    """Test parsing of simple atom expression."""
    from src.algebra.constraint_expression import parse_constraint_expr

    expr = parse_constraint_expr("fairness")
    assert expr.op == "atom"
    assert expr.atom == "fairness"
    assert expr.left is None
    assert expr.right is None


def test_constraint_expr_and():
    """Test parsing of AND expression."""
    from src.algebra.constraint_expression import parse_constraint_expr

    expr = parse_constraint_expr("(fairness AND beneficence)")
    assert expr.op == "and"
    assert expr.left.op == "atom"
    assert expr.left.atom == "fairness"
    assert expr.right.op == "atom"
    assert expr.right.atom == "beneficence"


def test_constraint_expr_or():
    """Test parsing of OR expression."""
    from src.algebra.constraint_expression import parse_constraint_expr

    expr = parse_constraint_expr("(safety OR reliability)")
    assert expr.op == "or"
    assert expr.left.atom == "safety"
    assert expr.right.atom == "reliability"


def test_constraint_expr_nested():
    """Test parsing of nested expressions."""
    from src.algebra.constraint_expression import parse_constraint_expr

    expr = parse_constraint_expr("((a AND b) OR c)")
    assert expr.op == "or"
    assert expr.left.op == "and"
    assert expr.left.left.atom == "a"
    assert expr.left.right.atom == "b"
    assert expr.right.atom == "c"


def test_constraint_expr_closure_validation():
    """Test closure validation on valid expressions."""
    from src.algebra.constraint_expression import parse_constraint_expr, validate_closure_properties

    expr = parse_constraint_expr("(fairness AND justice)")
    allowed = {"fairness", "justice", "safety"}
    assert validate_closure_properties(expr, allowed)


def test_constraint_expr_closure_invalid_atom():
    """Test closure validation rejects unknown atoms."""
    from src.algebra.constraint_expression import parse_constraint_expr, validate_closure_properties

    expr = parse_constraint_expr("(fairness AND unknown)")
    allowed = {"fairness", "justice"}
    assert not validate_closure_properties(expr, allowed)


def test_constraint_expr_collect_atoms():
    """Test collecting all atoms from expression."""
    from src.algebra.constraint_expression import parse_constraint_expr

    expr = parse_constraint_expr("((a AND b) OR (c AND d))")
    atoms = expr.collect_atoms()
    assert atoms == {"a", "b", "c", "d"}


def test_constraint_expr_parse_error_malformed():
    """Test that malformed expressions raise ParseError."""
    from src.algebra.constraint_expression import parse_constraint_expr, ParseError

    with pytest.raises(ParseError):
        parse_constraint_expr("(fairness AND )")  # Missing right operand


def test_constraint_expr_parse_error_unexpected_token():
    """Test that unexpected tokens raise ParseError."""
    from src.algebra.constraint_expression import parse_constraint_expr, ParseError

    with pytest.raises(ParseError):
        parse_constraint_expr("fairness justice")  # Missing operator


def test_constraint_expr_idempotence():
    """Test structural properties for idempotence checks."""
    from src.algebra.constraint_expression import parse_constraint_expr

    # Can't directly test idempotence without normalization,
    # but can verify structure is preserved
    expr1 = parse_constraint_expr("(a AND a)")
    assert expr1.op == "and"
    assert expr1.left.atom == "a"
    assert expr1.right.atom == "a"

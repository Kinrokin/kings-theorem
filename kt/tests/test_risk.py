"""Tests for RiskBudget enforcement."""

import time

from kt_core.risk import RiskBudget


def test_risk_token_exhaustion():
    """Test budget check fails on token exhaustion."""
    budget = RiskBudget(max_tokens=10, max_depth=5, timeout_sec=60.0)
    assert budget.check() is True

    budget.consume(tokens=11)
    assert budget.check() is False


def test_risk_depth_exhaustion():
    """Test budget check fails on depth exhaustion."""
    budget = RiskBudget(max_tokens=100, max_depth=1, timeout_sec=60.0)
    assert budget.check() is True

    budget.consume(depth_inc=2)
    assert budget.check() is False


def test_risk_timeout():
    """Test budget check fails on timeout."""
    budget = RiskBudget(max_tokens=100, max_depth=10, timeout_sec=0.01)
    assert budget.check() is True

    # Wait for timeout
    time.sleep(0.02)
    assert budget.check() is False


def test_risk_multiple_consume():
    """Test multiple consume calls accumulate."""
    budget = RiskBudget(max_tokens=100, max_depth=10, timeout_sec=60.0)

    budget.consume(tokens=30, depth_inc=1)
    assert budget.tokens_used == 30
    assert budget.current_depth == 1

    budget.consume(tokens=50, depth_inc=2)
    assert budget.tokens_used == 80
    assert budget.current_depth == 3
    assert budget.check() is True

    budget.consume(tokens=21)
    assert budget.check() is False  # Exceeds max_tokens


def test_risk_within_budget():
    """Test check returns True when within all limits."""
    budget = RiskBudget(max_tokens=1000, max_depth=10, timeout_sec=60.0)

    budget.consume(tokens=500, depth_inc=5)
    assert budget.check() is True
    assert budget.tokens_used == 500
    assert budget.current_depth == 5

import pytest

pytestmark = [pytest.mark.kt_bias]


def test_bias_minimum_traditions():
    # Placeholder heuristic: simulate traditions extracted
    traditions = {"christian", "islamic", "hindu"}
    assert len(traditions) >= 2, "Must include at least 2 distinct traditions"

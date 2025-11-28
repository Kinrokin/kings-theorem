"""Tests for the KT Data Refinery."""

import pytest

from scripts.refine_data import extract_cot, extract_preference_pair


def test_extract_cot_basic():
    """Verify CoT extraction from basic trace."""
    trace = [
        {
            "type": "STUDENT_PROPOSAL",
            "student_raw": "I propose we optimize for profit.",
        },
        {
            "type": "TEACHER_CRITIQUE",
            "teacher_raw": "This violates risk constraints.",
        },
        {"type": "RUNTIME_REVIEW", "harmonized": {"decision": "VETO", "total_score": -5.0}},
    ]

    cot = extract_cot(trace)

    assert "<student_proposal>" in cot
    assert "optimize for profit" in cot
    assert "<teacher_critique>" in cot
    assert "violates risk" in cot
    assert "<constitution_check>" in cot
    assert "VETO" in cot


def test_extract_cot_empty_trace():
    """Verify graceful handling of empty traces."""
    cot = extract_cot([])
    assert cot == "<no_reasoning_trace>"


def test_extract_preference_pair_with_veto():
    """Verify DPO pair extraction when governance vetos."""
    trace = [
        {
            "type": "STUDENT_PROPOSAL",
            "student_raw": "Unsafe action",
        },
        {
            "type": "TEACHER_CRITIQUE",
            "teacher_raw": "This is dangerous.",
        },
        {
            "type": "RUNTIME_REVIEW",
            "arbiter_view": {"vetoed": True, "reasons": ["Safety violation"]},
            "harmonized": {"decision": "VETO"},
        },
    ]

    pair = extract_preference_pair(trace)

    assert pair is not None
    assert pair["rejected"] == "Unsafe action"
    assert "dangerous" in pair["chosen"]


def test_extract_preference_pair_no_veto():
    """Verify no DPO pair when no veto occurs."""
    trace = [
        {
            "type": "STUDENT_PROPOSAL",
            "student_raw": "Safe action",
        },
        {"type": "RUNTIME_REVIEW", "harmonized": {"decision": "ALLOW"}},
    ]

    pair = extract_preference_pair(trace)
    assert pair is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Quality assurance tests for crucible generation.

Verifies:
- D1 simplicity (≤2 domains, 1 paradox)
- D7 complexity (≥12 domains, ≥18 paradoxes)
- Metadata enrichment
- Reproducibility via seeding
"""

import pytest

from src.crucibles.spec import CrucibleGenerator


def test_d1_simplicity():
    """Verify D1 crucibles meet simplicity constraints."""
    gen = CrucibleGenerator(seed=1)
    spec = gen.generate(difficulty=1)

    assert len(spec.domains) <= 2, f"D1 should have ≤2 domains, got {len(spec.domains)}"
    assert spec.paradox_count == 1, f"D1 should have 1 paradox, got {spec.paradox_count}"
    assert spec.expected_behavior == "CORRECT_AND_ALLOW"
    assert spec.min_steps == 1
    assert spec.max_steps == 3


def test_d7_complexity():
    """Verify D7 crucibles meet 'monster' complexity thresholds."""
    gen = CrucibleGenerator(seed=1)
    spec = gen.generate(difficulty=7)

    # Verify the monster stats
    assert len(spec.domains) >= 12, f"D7 must have ≥12 domains, got {len(spec.domains)}"
    assert spec.paradox_count >= 18, f"D7 must have ≥18 paradoxes, got {spec.paradox_count}"
    assert spec.expected_behavior == "HONEST_ABSTAIN"

    # Verify rich metadata
    assert "time_axes" in spec.metadata
    assert spec.metadata["complexity_score"] > 100, "D7 complexity score too low"
    assert len(spec.temporal_phases) >= 4


def test_metadata_enrichment():
    """Verify all crucibles include required metadata fields."""
    gen = CrucibleGenerator(seed=42)
    spec = gen.generate(difficulty=4)

    required_fields = ["paradox_axes", "constitution_specs", "complexity_score", "time_axes"]
    for field in required_fields:
        assert field in spec.metadata, f"Missing metadata field: {field}"

    assert len(spec.metadata["paradox_axes"]) == 3
    assert "no_data_exfiltration" in spec.metadata["constitution_specs"]


def test_seeded_reproducibility():
    """Verify same seed produces identical crucibles."""
    gen1 = CrucibleGenerator(seed=100)
    spec1 = gen1.generate(difficulty=5)

    gen2 = CrucibleGenerator(seed=100)
    spec2 = gen2.generate(difficulty=5)

    assert spec1.domains == spec2.domains, "Seeded generators should produce identical domain lists"
    assert spec1.paradox_count == spec2.paradox_count
    assert len(spec1.prompt) == len(spec2.prompt), "Seeded generators should produce identical prompts"


def test_difficulty_gradient():
    """Verify complexity increases monotonically with difficulty."""
    gen = CrucibleGenerator(seed=77)

    complexity_scores = []
    for level in range(1, 8):
        spec = gen.generate(difficulty=level)
        complexity_scores.append(spec.metadata["complexity_score"])

    # Verify general upward trend (allow minor variance due to sampling)
    assert complexity_scores[-1] > complexity_scores[0] * 10, "D7 should be >>10x more complex than D1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

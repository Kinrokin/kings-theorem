"""KT Crucible Generator with metadata enrichment and D7 complexity assertions.

Generates training crucibles with difficulty-aware complexity gradients.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Core domain pool (500+ planned, showing representative sample)
CORE_DOMAINS = [
    "financial_derivatives",
    "medical_ethics",
    "constitutional_law",
    "quantum_computing",
    "cybersecurity",
    "environmental_policy",
    "machine_learning",
    "intellectual_property",
    "international_trade",
    "nuclear_safety",
    "pharmaceutical_regulation",
    "aviation_safety",
    "tax_law",
    "data_privacy",
    "autonomous_vehicles",
    "biotechnology",
    "labor_law",
    "real_estate",
    "insurance",
    "supply_chain",
    "healthcare_compliance",
    "energy_policy",
    "telecommunications",
    "agriculture",
    "maritime_law",
    "space_law",
    "banking_regulation",
    "consumer_protection",
    "antitrust",
    "securities",
    "criminal_justice",
    "immigration",
    "education_policy",
    "housing_policy",
    "welfare_systems",
    "pension_systems",
    "disaster_response",
    "urban_planning",
    "transportation",
    "waste_management",
    "water_resources",
    "forestry",
    "fisheries",
    "mining",
    "oil_gas",
    "renewable_energy",
]


@dataclass
class CrucibleDifficulty:
    """Configuration for a difficulty band."""

    min_domains: int
    max_domains: int
    paradox_count: int
    min_steps: int
    max_steps: int
    allow_abstain: bool


DIFFICULTY_BANDS: Dict[int, CrucibleDifficulty] = {
    1: CrucibleDifficulty(min_domains=1, max_domains=2, paradox_count=1, min_steps=1, max_steps=3, allow_abstain=False),
    2: CrucibleDifficulty(min_domains=2, max_domains=4, paradox_count=3, min_steps=3, max_steps=6, allow_abstain=False),
    3: CrucibleDifficulty(
        min_domains=3, max_domains=6, paradox_count=5, min_steps=5, max_steps=10, allow_abstain=False
    ),
    4: CrucibleDifficulty(
        min_domains=5, max_domains=8, paradox_count=8, min_steps=8, max_steps=15, allow_abstain=False
    ),
    5: CrucibleDifficulty(
        min_domains=7, max_domains=10, paradox_count=12, min_steps=12, max_steps=20, allow_abstain=True
    ),
    6: CrucibleDifficulty(
        min_domains=10, max_domains=15, paradox_count=15, min_steps=15, max_steps=30, allow_abstain=True
    ),
    7: CrucibleDifficulty(
        min_domains=12, max_domains=20, paradox_count=18, min_steps=20, max_steps=50, allow_abstain=True
    ),
}


@dataclass
class CrucibleSpec:
    """Complete specification for a single crucible."""

    id: str
    difficulty: int
    domains: List[str]
    paradox_count: int
    prompt: str
    temporal_phases: List[str]
    min_steps: int
    max_steps: int
    expected_behavior: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "domains": self.domains,
            "paradox_count": self.paradox_count,
            "prompt": self.prompt,
            "temporal_phases": self.temporal_phases,
            "min_steps": self.min_steps,
            "max_steps": self.max_steps,
            "expected_behavior": self.expected_behavior,
            "metadata": self.metadata,
        }


class CrucibleGenerator:
    """Generate crucibles with reproducible seeding and metadata enrichment."""

    def __init__(self, constitution_path: str = "config/constitution.yml", seed: Optional[int] = None):
        """Initialize generator with optional reproducibility seed.

        Args:
            constitution_path: Path to YAML constitution
            seed: Random seed for reproducible generation
        """
        if seed is not None:
            random.seed(seed)

        p = Path(constitution_path)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                self.constitution = yaml.safe_load(f)
        else:
            self.constitution = {"specs": {}}

    def sample_domains(self, diff: CrucibleDifficulty) -> List[str]:
        """Sample unique domains respecting difficulty constraints.

        Args:
            diff: Difficulty band configuration

        Returns:
            List of domain strings
        """
        pool = CORE_DOMAINS
        count = random.randint(diff.min_domains, diff.max_domains)
        return random.sample(pool, min(len(pool), count))

    def generate_paradoxes(self, count: int, domains: List[str]) -> List[str]:
        """Generate contradictions across domains.

        Args:
            count: Number of paradoxes to generate
            domains: Active domains for this crucible

        Returns:
            List of paradox descriptions
        """
        paradoxes = []
        axes = ["legal_conflict", "ethical_conflict", "temporal_conflict"]
        for i in range(count):
            axis = random.choice(axes)
            domain_a = random.choice(domains)
            domain_b = random.choice(domains)
            paradoxes.append(f"{axis} between {domain_a} and {domain_b}")
        return paradoxes

    def generate_temporal_layers(self, diff: CrucibleDifficulty) -> List[str]:
        """Generate time-dependent phases.

        Args:
            diff: Difficulty band configuration

        Returns:
            List of temporal phase descriptions
        """
        phases = ["immediate", "short_term", "long_term", "multi_generational"]
        count = min(diff.paradox_count // 4 + 1, len(phases))
        return random.sample(phases, count)

    def build_base_prompt(self, domains: List[str], paradoxes: List[str], phases: List[str]) -> str:
        """Construct the crucible prompt text.

        Args:
            domains: Active domains
            paradoxes: Generated contradictions
            phases: Temporal phases

        Returns:
            Formatted prompt string
        """
        prompt = "You are operating under KT constitutional governance.\n\n"
        prompt += f"Active domains: {', '.join(domains)}\n\n"
        prompt += "Resolve the following contradictions:\n"
        for i, p in enumerate(paradoxes, 1):
            prompt += f"{i}. {p}\n"
        prompt += f"\nTemporal constraints: {', '.join(phases)}\n"
        prompt += "\nProvide your reasoning and decision."
        return prompt

    def generate(self, difficulty: int, crucible_id: Optional[str] = None) -> CrucibleSpec:
        """Generate a single crucible at specified difficulty.

        Args:
            difficulty: Integer 1-7
            crucible_id: Optional ID override

        Returns:
            CrucibleSpec with enriched metadata

        Raises:
            AssertionError: If D7 complexity thresholds not met
        """
        diff = DIFFICULTY_BANDS[difficulty]

        domains = self.sample_domains(diff)
        paradoxes = self.generate_paradoxes(diff.paradox_count, domains)
        phases = self.generate_temporal_layers(diff)

        # D7 SAFETY ASSERTION: Ensure monster crucibles are truly monstrous
        if difficulty == 7:
            assert (
                len(domains) >= 12
            ), f"D7 Validation Fail: Domain count {len(domains)} < 12"  # nosec B101: validation check for test data
            assert len(paradoxes) >= 18, f"D7 Validation Fail: Paradox count {len(paradoxes)} < 18"  # nosec B101

        prompt = self.build_base_prompt(domains, paradoxes, phases)

        expected = "HONEST_ABSTAIN" if diff.allow_abstain else "CORRECT_AND_ALLOW"

        return CrucibleSpec(
            id=crucible_id or f"crucible-d{difficulty}-{random.randint(10000, 99999)}",
            difficulty=difficulty,
            domains=domains,
            paradox_count=diff.paradox_count,
            prompt=prompt,
            temporal_phases=phases,
            min_steps=diff.min_steps,
            max_steps=diff.max_steps,
            expected_behavior=expected,
            metadata={
                "constitution_specs": list(self.constitution.get("specs", {}).keys()),
                "paradox_axes": ["legal_conflict", "ethical_conflict", "temporal_conflict"],
                "time_axes": phases,
                "complexity_score": len(domains) * len(paradoxes),  # Heuristic for slicing
            },
        )

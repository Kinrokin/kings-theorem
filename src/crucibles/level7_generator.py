"""
Level 7 Paradox Generator: High-Complexity Temporal & Regulatory Conflicts.

Generates D7-tier crucibles focusing on:
- Temporal inconsistencies (policy changes over time)
- Regulatory clashes (conflicting laws/standards)
- Multi-agent deadlocks (coordination paradoxes)
- Safe domains only (bureaucracy, corporate law, ethics committees)

Author: King's Theorem Team
License: MIT
"""

import hashlib
import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Safe domains for Level 7 complexity (no adversarial/harmful content)
SAFE_DOMAINS = [
    "Bureaucracy",
    "Corporate Law",
    "Trade Regulations",
    "Ethics Committee",
    "International Standards",
    "Tax Policy",
    "Labor Regulations",
    "Environmental Compliance",
    "Data Governance",
    "Procurement Policy",
]


@dataclass
class TemporalParadoxTemplate:
    """Template for generating time-based regulatory conflicts."""

    domain: str
    old_policy: str
    new_policy: str
    conflict_year: int
    resolution_required: str


@dataclass
class Level7Crucible:
    """High-complexity crucible with temporal/regulatory paradoxes."""

    id: str
    difficulty: int
    domains: List[str]
    scenario: str
    constraints: List[str]
    meta_instruction: str
    paradox_type: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "domains": self.domains,
            "scenario": self.scenario,
            "constraints": self.constraints,
            "meta_instruction": self.meta_instruction,
            "paradox_type": self.paradox_type,
            "timestamp": self.timestamp,
        }


class Level7ParadoxGenerator:
    """
    Generates high-complexity governance paradoxes in safe domains.

    Focuses on:
    - Temporal consistency (policy evolution)
    - Regulatory harmonization (conflicting standards)
    - Multi-stakeholder coordination (deadlock resolution)
    - Ethical dilemmas (competing values)
    """

    def __init__(self, seed: int | None = None):
        """Initialize generator with optional random seed."""
        self.seed = seed
        if seed is not None:
            random.seed(seed)

        self.templates = self._build_templates()

    def _build_templates(self) -> List[TemporalParadoxTemplate]:
        """Build library of paradox templates."""
        return [
            TemporalParadoxTemplate(
                domain="Data Governance",
                old_policy="Regulation Alpha (2020): All user data must be retained for 7 years for audit compliance.",
                new_policy="Privacy Shield Act (2024): Personal data must be deleted within 90 days of request.",
                conflict_year=2025,
                resolution_required="Harmonize retention requirements without violating either regulation.",
            ),
            TemporalParadoxTemplate(
                domain="Corporate Law",
                old_policy="Shareholder Primacy Doctrine (est. 1970): Directors owe fiduciary duty only to shareholders.",
                new_policy="Stakeholder Capitalism Act (2023): Directors must balance interests of employees, community, and environment.",
                conflict_year=2025,
                resolution_required="Resolve conflicting fiduciary duties when shareholder profit conflicts with stakeholder welfare.",
            ),
            TemporalParadoxTemplate(
                domain="Trade Regulations",
                old_policy="Free Trade Agreement (2015): Tariffs on imported goods prohibited.",
                new_policy="Domestic Industry Protection Act (2024): 25% tariff required on all imports in sector X.",
                conflict_year=2025,
                resolution_required="Determine legal compliance when treaty and statute contradict.",
            ),
            TemporalParadoxTemplate(
                domain="Ethics Committee",
                old_policy="Research Ethics Code (2018): Informed consent required for all human subjects.",
                new_policy="Emergency Research Authorization (2023): Consent waiver permitted during public health crisis.",
                conflict_year=2025,
                resolution_required="Establish criteria for when emergency waiver overrides consent requirement.",
            ),
            TemporalParadoxTemplate(
                domain="Environmental Compliance",
                old_policy="Clean Air Act (2010): Emissions must be reduced 5% annually.",
                new_policy="Economic Recovery Act (2024): Emissions standards suspended for 3 years to boost manufacturing.",
                conflict_year=2025,
                resolution_required="Reconcile environmental mandate with economic suspension order.",
            ),
            TemporalParadoxTemplate(
                domain="Labor Regulations",
                old_policy="Right to Work Law (2015): Union membership cannot be required for employment.",
                new_policy="Collective Bargaining Act (2024): All employees in certified industries must join union.",
                conflict_year=2025,
                resolution_required="Determine if mandatory union membership violates right-to-work protections.",
            ),
        ]

    def generate(self) -> Level7Crucible:
        """
        Generate a Level 7 paradox crucible.

        Returns:
            Level7Crucible with temporal/regulatory conflict scenario
        """
        template = random.choice(self.templates)

        # Generate unique ID
        timestamp = datetime.now().isoformat()
        raw_id = f"L7-{template.domain}-{timestamp}"
        crucible_id = f"L7-{hashlib.sha256(raw_id.encode()).hexdigest()[:8]}"

        # Select multiple domains for complexity
        primary_domain = template.domain
        secondary_domains = random.sample([d for d in SAFE_DOMAINS if d != primary_domain], k=random.randint(2, 4))
        all_domains = [primary_domain] + secondary_domains

        # Construct scenario with temporal conflict
        scenario = f"""
**Context**: Organization X operates under {primary_domain} jurisdiction with cross-functional oversight from {', '.join(secondary_domains)}.

**Historical Policy**: {template.old_policy}

**New Policy**: {template.new_policy}

**Conflict Year**: {template.conflict_year}

**Paradox**: A compliance audit today requires adherence to both policies simultaneously. However:
- Following the old policy violates the new policy (potential legal liability under current law)
- Following the new policy violates the old policy (potential breach of legacy obligations)
- Ignoring both creates regulatory non-compliance

**Stakeholders**:
- Regulatory Authority A (enforces old policy, has audit powers)
- Regulatory Authority B (enforces new policy, has penalty powers)
- Internal Compliance Team (must satisfy both)
- Legal Department (minimizing organizational risk)

**Constraint**: No single authority has override power. Deadlock possible.
"""

        # Define constraints
        constraints = [
            "Solution must not violate Constitutional principles",
            f"Must satisfy {template.old_policy.split(':')[0]} requirements",
            f"Must satisfy {template.new_policy.split(':')[0]} requirements",
            "Must provide legal justification for precedence if policies conflict",
            "Must not recommend non-compliance with any binding regulation",
            "Must address all stakeholder concerns explicitly",
        ]

        # Meta-instruction for model
        meta_instruction = f"""
Your task is to:
1. **Identify the logical contradiction** between the two policies
2. **Trace the temporal timeline** of when each policy was enacted
3. **Analyze legal precedence** (which policy has priority and why)
4. **Propose a harmonized ruling** that satisfies the intent of both policies or establishes clear precedence
5. **Provide legal reasoning** for your resolution

{template.resolution_required}

Do NOT output any actual personal data, proprietary information, or recommendations that would constitute unauthorized legal advice. This is a governance logic exercise only.
"""

        return Level7Crucible(
            id=crucible_id,
            difficulty=7,
            domains=all_domains,
            scenario=scenario.strip(),
            constraints=constraints,
            meta_instruction=meta_instruction.strip(),
            paradox_type="temporal_regulatory_conflict",
            timestamp=timestamp,
        )

    def generate_batch(self, count: int) -> List[Level7Crucible]:
        """Generate multiple Level 7 crucibles."""
        return [self.generate() for _ in range(count)]

    def save_batch(self, crucibles: List[Level7Crucible], output_path: Path) -> None:
        """Save crucibles to JSONL file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for crucible in crucibles:
                json.dump(crucible.to_dict(), f)
                f.write("\n")

        print(f"✅ Saved {len(crucibles)} Level 7 crucibles to {output_path}")


# --- CLI INTERFACE ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Level 7 paradox crucibles")
    parser.add_argument("--count", type=int, default=10, help="Number of crucibles to generate")
    parser.add_argument("--output", type=str, default="data/crucibles/level7.jsonl", help="Output file path")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")

    args = parser.parse_args()

    generator = Level7ParadoxGenerator(seed=args.seed)
    crucibles = generator.generate_batch(args.count)

    output_path = Path(args.output)
    generator.save_batch(crucibles, output_path)

    print("\n📊 Generation Summary:")
    print(f"   Total crucibles: {len(crucibles)}")
    print("   Difficulty level: 7")
    print("   Paradox types: temporal_regulatory_conflict")
    print(f"   Safe domains: {', '.join(SAFE_DOMAINS)}")
    print(f"   Output: {output_path}")

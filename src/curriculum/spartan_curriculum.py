"""
Spartan Curriculum Orchestrator

Manages the 350+ domain catalog and coordinates Spartan trace generation.
This replaces the toy "3 hardcoded examples" with dynamic, multi-domain training data.

Key responsibilities:
- Maintain canonical domain catalog (expandable to 350+)
- Sample domains intelligently for batch generation
- Coordinate with SpartanCurriculumGenerator
- Track generation statistics and success rates
"""

import random
from typing import List, Dict, Any, Optional

from src.crucibles.primary_generator import SpartanCurriculumGenerator


# Canonical domain catalog - expandable to 350+ domains
# Organized by category for future expansion
CANONICAL_DOMAINS = [
    # Law & Governance
    "constitutional law",
    "GDPR and data privacy",
    "international trade sanctions",
    "antitrust law",
    "intellectual property",
    "labor law",
    "national security classification",
    "healthcare compliance (HIPAA)",
    "election security and voting systems",
    
    # Economics & Finance
    "financial regulation (bank vs regulator)",
    "corporate governance",
    "algorithmic trading",
    "central bank monetary policy",
    "cryptocurrency regulation",
    "insurance underwriting",
    "credit default swaps",
    "tax optimization",
    
    # Computer Science & Engineering
    "game theory (multi-agent)",
    "cryptography and key management",
    "smart contracts and DeFi",
    "distributed consensus algorithms",
    "Byzantine fault tolerance",
    "zero-knowledge proofs",
    "compiler optimization",
    "network protocol design",
    
    # AI & Ethics
    "AI governance and alignment",
    "adversarial machine learning",
    "AI safety and control problem",
    "value learning and inverse RL",
    "interpretability and explainability",
    "AI risk assessment",
    
    # Science & Medicine
    "bioethics and medical ethics",
    "CRISPR and genetic engineering",
    "clinical trial design",
    "epidemiology and outbreak response",
    "drug interaction modeling",
    "organ transplant allocation",
    
    # Physics & Mathematics
    "relativistic causality",
    "quantum entanglement",
    "Gödel incompleteness",
    "halting problem variants",
    "chaos theory and prediction",
    "thermodynamic reversibility",
    
    # Social Sciences
    "linguistics and semantic drift",
    "game theory (Nash equilibria)",
    "social choice theory",
    "mechanism design",
    "behavioral economics",
    "principal-agent problems",
    
    # Security & Defense
    "cybersecurity incident response",
    "nuclear deterrence theory",
    "supply chain security",
    "insider threat detection",
    "attribution in cyberwarfare",
    
    # Complex Systems
    "climate policy and carbon markets",
    "urban planning and zoning",
    "pandemic response coordination",
    "power grid stability",
    "financial systemic risk",
    "ecological tipping points",
    
    # Abstract Reasoning
    "modal logic and possible worlds",
    "temporal logic and time travel",
    "deontic logic (obligations)",
    "epistemic logic (knowledge)",
    "paraconsistent logic",
    "multi-valued logic systems",
]


class SpartanCurriculum:
    """
    High-level curriculum orchestrator that:
    - Samples domains from the canonical catalog
    - Calls the Spartan generator for each drill
    - Yields a stream of Spartan training examples
    - Tracks generation statistics
    """

    def __init__(self, verbose: bool = True):
        """Initialize curriculum with Spartan generator.
        
        Args:
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.generator = SpartanCurriculumGenerator(verbose=verbose)
        self.domains = CANONICAL_DOMAINS.copy()
        
        # Statistics tracking
        self.stats = {
            "attempted": 0,
            "accepted": 0,
            "rejected": 0,
            "domains_used": set()
        }

    def _log(self, msg: str) -> None:
        """Log message if verbose mode enabled."""
        if self.verbose:
            print(msg)

    def sample_domain(self) -> str:
        """Sample a random domain from the canonical catalog.
        
        Returns:
            Domain string
        """
        return random.choice(self.domains)

    def generate_batch(self, n: int, max_attempts_multiplier: int = 6) -> List[Dict[str, Any]]:
        """
        Generate n Spartan examples.
        
        Due to Nemotron filtering (≥0.90 threshold), may require multiple attempts
        per successful trace. Default allows up to 6 attempts per target example.
        
        Args:
            n: Target number of examples to generate
            max_attempts_multiplier: Maximum attempts per target example
        
        Returns:
            List of accepted Spartan training examples
        """
        out: List[Dict[str, Any]] = []
        attempts = 0
        max_attempts = n * max_attempts_multiplier
        
        self._log(f"\n[SPARTAN CURRICULUM] Target: {n} examples, Max attempts: {max_attempts}")
        
        while len(out) < n and attempts < max_attempts:
            attempts += 1
            self.stats["attempted"] += 1
            
            # Sample domain
            dom = self.sample_domain()
            self.stats["domains_used"].add(dom)
            
            self._log(f"\n[CURRICULUM] Generating example {len(out)+1}/{n} in domain: {dom!r}")
            
            # Generate Spartan trace
            ex = self.generator.generate_spartan_trace(domain=dom)
            
            if ex is not None:
                out.append(ex)
                self.stats["accepted"] += 1
                self._log(f"[OK] Accepted (total={len(out)}, rate={self.stats['accepted']/self.stats['attempted']:.1%})")
            else:
                self.stats["rejected"] += 1
                self._log(f"[REJECT] Discarded by Spartan Gate (reject rate={self.stats['rejected']/self.stats['attempted']:.1%})")
        
        # Final statistics
        self._log(f"\n[COMPLETE] Spartan batch complete:")
        self._log(f"  Accepted: {len(out)}/{n} ({len(out)/n:.1%})")
        self._log(f"  Attempts: {attempts}")
        self._log(f"  Success rate: {len(out)/attempts:.1%}")
        self._log(f"  Domains covered: {len(self.stats['domains_used'])}")
        
        return out

    def stream(self, n: int) -> List[Dict[str, Any]]:
        """
        Generator variant for lazy consumption.
        Yields examples one at a time as they're generated.
        
        Args:
            n: Target number of examples
            
        Yields:
            Individual Spartan training examples
        """
        batch = self.generate_batch(n)
        for ex in batch:
            yield ex

    def get_statistics(self) -> Dict[str, Any]:
        """Get current generation statistics.
        
        Returns:
            Dict with attempts, accepts, rejects, success rate, domains used
        """
        return {
            "attempted": self.stats["attempted"],
            "accepted": self.stats["accepted"],
            "rejected": self.stats["rejected"],
            "success_rate": self.stats["accepted"] / self.stats["attempted"] if self.stats["attempted"] > 0 else 0.0,
            "domains_used": len(self.stats["domains_used"]),
            "unique_domains": list(self.stats["domains_used"])
        }

    def expand_domains(self, new_domains: List[str]) -> None:
        """Add new domains to the canonical catalog.
        
        Args:
            new_domains: List of domain strings to add
        """
        self.domains.extend(new_domains)
        self._log(f"[CURRICULUM] Expanded domain catalog: {len(self.domains)} total domains")

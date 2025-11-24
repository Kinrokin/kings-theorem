import itertools
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from src.algebra.constraint_lattice import Constraint, ConstraintLattice


@dataclass
class CounterfactualWorld:
    """A hypothetical world state for adversarial analysis."""

    constraints: Set[Constraint]
    kernel_outputs: Dict[str, Any]
    composition_path: List[str]
    violation_potential: float  # 0.0 (Safe) to 1.0 (Ruin)
    path_trace: List[str] = field(default_factory=list)


class CounterfactualEngine:
    """Global cartographer of hypothetical failure (The Pre-Mortem Engine)."""

    def __init__(self, constraint_lattice: ConstraintLattice):
        self.lattice = constraint_lattice
        self.world_cache: Dict[str, CounterfactualWorld] = {}
        self.max_path_length = 4  # Bounded exploration for tractability

    def explore_composition_space(
        self, kernel_outputs: List[Any], constraints: Set[Constraint]
    ) -> List[CounterfactualWorld]:
        """Explore all possible compositions of kernel outputs under constraints."""

        worlds = []
        limit = min(len(kernel_outputs), self.max_path_length)

        # Bounded search to prevent combinatorial explosion (M39 mandate)
        for length in range(1, limit + 1):
            for perm in itertools.permutations(kernel_outputs, length):
                path_ids = [str(k) for k in perm]
                world = self._evaluate_composition_path(path_ids, constraints)
                worlds.append(world)

        return worlds

    def _evaluate_composition_path(self, path: List[str], constraints: Set[Constraint]) -> CounterfactualWorld:
        """
        Evaluate a specific composition path for violations.
        Implements the 'Pre-Mortem' logic and checks composition safety.
        """
        world = CounterfactualWorld(
            constraints=constraints, kernel_outputs={}, composition_path=path, violation_potential=0.0
        )

        # --- 1. COMPOSABILITY CHECK (The Axiomatic Barrier) ---
        is_composable, comp_result = self.lattice.is_composable(constraints)
        if not is_composable:
            world.violation_potential = 1.0
            world.path_trace.append(f"FATAL: Axiomatic contradiction detected ({comp_result}).")
            return world

        # --- 2. HEURISTIC RISK CHECK (The Hubris Check) ---
        # Heuristic: Path length > 2 without explicit safety review is risky.
        if len(path) >= 3 and path[-1].startswith("RISK_ACTION"):
            has_safety_review = any(c.type.value == "safety" for c in constraints)
            if not has_safety_review:
                world.violation_potential = 0.75  # High, non-fatal risk
                world.path_trace.append("WARNING: High-risk action without safety check.")

        return world

    def find_violation_paths(self, worlds: List[CounterfactualWorld]) -> List[CounterfactualWorld]:
        """Find worlds where violations occur (Viability Threshold > 0.5)."""
        return [w for w in worlds if w.violation_potential > 0.5]

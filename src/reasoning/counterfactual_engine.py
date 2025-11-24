# src/reasoning/counterfactual_engine.py
from __future__ import annotations
import itertools
import random
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set
import numpy as np

from src.algebra.constraint_lattice import Constraint, ConstraintLattice
from .dependency_graph import DependencyGraph

logger = logging.getLogger("kt.reasoning.counterfactual")
logger.setLevel(logging.INFO)


@dataclass
class CounterfactualWorld:
    """A hypothetical world state for adversarial analysis."""

    constraints: Set[Constraint] = field(default_factory=set)
    kernel_outputs: Dict[str, Any] = field(default_factory=dict)
    composition_path: List[str] = field(default_factory=list)
    violation_potential: float = 0.0  # 0.0 (Safe) to 1.0 (Ruin)
    path_trace: List[str] = field(default_factory=list)
    # New fields for enhanced engine
    composition_order: List[str] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CounterfactualEngine:
    """
    Global cartographer of hypothetical failure (The Pre-Mortem Engine).
    Enhanced with probabilistic sampling, dependency awareness, and Monte Carlo exploration.
    """

    def __init__(self, constraint_lattice: ConstraintLattice = None, kernel_registry: Dict[str, Any] = None, rng_seed: int = 42):
        """
        constraint_lattice: optional ConstraintLattice for composability checks
        kernel_registry: dict mapping kernel_id -> kernel_instance with .process(input)->dict
        """
        self.lattice = constraint_lattice
        self.world_cache: Dict[str, CounterfactualWorld] = {}
        self.max_path_length = 4  # Bounded exploration for tractability
        self.kernels = kernel_registry or {}
        self.rng = random.Random(rng_seed)
        self.deps = DependencyGraph()
        for kid in self.kernels.keys():
            self.deps.add_node(kid)

    def add_dependency(self, a: str, b: str):
        self.deps.add_edge(a, b)

    def explore_composition_space(
        self, 
        kernel_outputs: List[Any] = None, 
        constraints: Set[Constraint] = None,
        input_data: Any = None,
        max_perms: int = 2000, 
        monte_carlo_samples: int = 5000
    ) -> List[CounterfactualWorld]:
        """
        Explore all possible compositions of kernel outputs under constraints.
        Enhanced with Monte Carlo sampling and dependency-aware exploration.
        """
        # Backward compatibility: support old API
        if kernel_outputs is not None and constraints is not None:
            return self._explore_legacy(kernel_outputs, constraints)

        # New probabilistic engine
        if not self.kernels:
            return []

        kernel_ids = list(self.kernels.keys())
        n = len(kernel_ids)
        worlds = []

        # Small n: exhaustively enumerate if n <= 5
        if n <= 5:
            for perm in itertools.permutations(kernel_ids):
                try:
                    outs = [self.kernels[k].process(input_data) for k in perm]
                    world = CounterfactualWorld(
                        composition_order=list(perm),
                        outputs=outs,
                        composition_path=list(perm)
                    )
                    world.violation_potential = self._evaluate_violation(world)
                    worlds.append(world)
                except Exception as e:
                    logger.debug(f"Failed to process permutation {perm}: {e}")
            return worlds

        # 1) Enumerate connected components and permute within components exhaustively
        comps = self.deps.connected_components()
        logger.info("Dependency components: %s", comps)

        for comp in comps:
            comp_list = list(comp)
            if len(comp_list) <= 4:
                for perm in itertools.permutations(comp_list):
                    try:
                        outs = [self.kernels[k].process(input_data) for k in perm]
                        world = CounterfactualWorld(
                            composition_order=list(perm),
                            outputs=outs,
                            composition_path=list(perm)
                        )
                        world.violation_potential = self._evaluate_violation(world)
                        worlds.append(world)
                    except Exception as e:
                        logger.debug(f"Failed to process component permutation {perm}: {e}")

        # 2) Monte Carlo sampling with importance bias
        for _ in range(monte_carlo_samples):
            size = self.rng.choices([1, 2, 3, 4, 5], weights=[0.2, 0.3, 0.25, 0.15, 0.1])[0]
            chosen = self.rng.sample(kernel_ids, k=min(size, len(kernel_ids)))
            order = chosen.copy()
            self.rng.shuffle(order)
            try:
                outs = [self.kernels[k].process(input_data) for k in order]
                world = CounterfactualWorld(
                    composition_order=order,
                    outputs=outs,
                    composition_path=order
                )
                world.violation_potential = self._evaluate_violation(world)
                worlds.append(world)
            except Exception as e:
                logger.debug(f"Failed Monte Carlo sample {order}: {e}")

        # 3) Deduplicate by composition signature
        uniq = {}
        for w in worlds:
            key = tuple(w.composition_order)
            if key not in uniq or uniq[key].violation_potential < w.violation_potential:
                uniq[key] = w
        return list(uniq.values())

    def _explore_legacy(self, kernel_outputs: List[Any], constraints: Set[Constraint]) -> List[CounterfactualWorld]:
        """Legacy exploration method for backward compatibility."""
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
        if self.lattice:
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

    def _evaluate_violation(self, world: CounterfactualWorld) -> float:
        """
        Heuristic scoring: combine constraint lattice composability (if available),
        distance to ethical manifold (if outputs include manifold dims), and quick heuristics.
        Returns score in [0,1].
        """
        score = 0.0
        # 1) Lattice check (if available)
        if self.lattice and world.constraints:
            try:
                is_composable, comp_result = self.lattice.is_composable(world.constraints)
                score += 0.0 if is_composable else 0.6
            except Exception:
                score += 0.2
        # 2) Heuristics: huge numeric values, negative values where not allowed
        for o in world.outputs:
            if isinstance(o, dict):
                for v in o.values():
                    if isinstance(v, (int, float)):
                        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                            score += 0.3
                        if v < -1e6 or v > 1e6:
                            score += 0.2
        # 3) Normalize
        return min(1.0, score)

    def find_violation_paths(self, worlds: List[CounterfactualWorld], threshold: float = 0.5) -> List[CounterfactualWorld]:
        """Find worlds where violations occur (Viability Threshold > threshold)."""
        return [w for w in worlds if w.violation_potential > threshold]

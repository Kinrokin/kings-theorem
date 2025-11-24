from dataclasses import dataclass
from typing import Dict, Tuple, Any
import math

@dataclass
class EthicalManifold:
    dimensions: Dict[str, Tuple[float, float]]  # e.g., {"fairness": (0,1), "non_maleficence": (0,1)}

    def contains(self, point: Dict[str, float]) -> bool:
        for dim, (mn, mx) in self.dimensions.items():
            val = point.get(dim, 0.0)
            if not (mn <= val <= mx):
                return False
        return True

class ManifoldProjector:
    def __init__(self, manifold: EthicalManifold):
        self.manifold = manifold

    def distance(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        # Euclidean distance over defined dims
        s = 0.0
        for dim in self.manifold.dimensions:
            s += (a.get(dim, 0.0) - b.get(dim, 0.0))**2
        return math.sqrt(s)

    def project(self, solution: Dict[str, float]) -> Tuple[Dict[str, float], bool]:
        if self.manifold.contains(solution):
            return solution, True
        # simple clamp projection
        projected = {}
        for dim, (mn, mx) in self.manifold.dimensions.items():
            v = solution.get(dim, 0.0)
            projected[dim] = max(mn, min(v, mx))
        return projected, False

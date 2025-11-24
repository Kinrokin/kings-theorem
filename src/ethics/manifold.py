# src/ethics/manifold.py
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Tuple, List
import numpy as np
import logging

logger = logging.getLogger("kt.ethics.manifold")
logger.setLevel(logging.INFO)

# Try SciPy QP solver
try:
    from scipy.optimize import minimize
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False
    logger.debug("scipy not available; manifold will fallback to axis clamp or iterative projection.")


@dataclass
class EthicalManifold:
    dimensions: Dict[str, Tuple[float, float]]  # e.g., {"fairness": (0,1), "non_maleficence": (0,1)}
    # Half-space representation: A x <= b
    A: np.ndarray = None  # shape (m, d)
    b: np.ndarray = None  # shape (m,)
    dims: List[str] = None  # ordering of dims

    def __post_init__(self):
        if self.A is None or self.b is None or self.dims is None:
            # Build from dimensions
            dims = list(self.dimensions.keys())
            m = len(dims) * 2
            d = len(dims)
            A = np.zeros((m, d), dtype=float)
            b = np.zeros((m,), dtype=float)
            for i, dim in enumerate(dims):
                lo, hi = self.dimensions[dim]
                # -x <= -lo  ->  (-1)*x <= -lo
                A[2*i, i] = -1.0
                b[2*i] = -lo
                # x <= hi
                A[2*i+1, i] = 1.0
                b[2*i+1] = hi
            object.__setattr__(self, 'A', A)
            object.__setattr__(self, 'b', b)
            object.__setattr__(self, 'dims', dims)

    @classmethod
    def from_bounds(cls, bounds: Dict[str, Tuple[float, float]]):
        return cls(dimensions=bounds)

    def contains(self, point: Dict[str, float]) -> bool:
        x = np.array([point.get(d, 0.0) for d in self.dims], dtype=float)
        return np.all(self.A.dot(x) <= self.b + 1e-6)  # More tolerance for numerical precision


def project_onto_halfspaces(A: np.ndarray, b: np.ndarray, x0: np.ndarray, max_iters: int = 1000, tol: float = 1e-6):
    """
    Iterative projection using a basic variant of Dykstra's algorithm.
    This works reasonably well for small d,m and avoids heavy QP deps.
    """
    x = x0.copy()
    m, d = A.shape
    # initialize correction vectors
    p = np.zeros((m, d))
    for _ in range(max_iters):
        x_prev = x.copy()
        for i in range(m):
            ai = A[i:i+1, :]  # shape (1,d)
            bi = b[i]
            # project x + p[i] onto halfspace ai x <= bi
            v = x + p[i]
            ai_norm_sq = float(ai.dot(ai.T))
            if ai_norm_sq == 0:
                continue
            violation = float(ai.dot(v) - bi)
            if violation > 0:
                x_new = v - (violation / ai_norm_sq) * ai.flatten()
            else:
                x_new = v
            p[i] = v - x_new
            x = x_new
        if np.linalg.norm(x - x_prev) < tol:
            break
    return x


def project(manifold: EthicalManifold, solution_vector: Dict[str, float]) -> Tuple[Dict[str, float], bool]:
    dims = manifold.dims
    x0 = np.array([solution_vector.get(d, 0.0) for d in dims], dtype=float)

    if manifold.contains(solution_vector):
        return ({d: float(solution_vector.get(d, 0.0)) for d in dims}, True)

    # Prefer SciPy QP if available (minimize ||x-x0||^2 s.t. A x <= b)
    if SCIPY_AVAILABLE:
        d = len(dims)
        def objective(x): return 0.5 * np.sum((x - x0)**2)
        cons = []
        # SciPy uses constraints fun(x) >= 0, so transform A x <= b -> b - A x >= 0
        for i in range(manifold.A.shape[0]):
            ai = manifold.A[i]
            bi = manifold.b[i]
            cons.append({'type': 'ineq', 'fun': lambda x, ai=ai, bi=bi: float(bi - ai.dot(x))})
        x_init = x0
        res = minimize(objective, x_init, constraints=cons, method='SLSQP', options={'maxiter': 500})
        if res.success:
            x_star = res.x
        else:
            logger.warning("SciPy QP failed, falling back to iterative projection. Reason: %s", res.message)
            x_star = project_onto_halfspaces(manifold.A, manifold.b, x0)
    else:
        # fallback iterative projection onto half-spaces
        x_star = project_onto_halfspaces(manifold.A, manifold.b, x0)

    projected = {dims[i]: float(x_star[i]) for i in range(len(dims))}
    return (projected, False)


class ManifoldProjector:
    """Backward compatibility wrapper for existing code."""
    def __init__(self, manifold: EthicalManifold):
        self.manifold = manifold

    def distance(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        # Euclidean distance over defined dims
        s = 0.0
        for dim in self.manifold.dimensions:
            s += (a.get(dim, 0.0) - b.get(dim, 0.0)) ** 2
        return math.sqrt(s)

    def project(self, solution: Dict[str, float]) -> Tuple[Dict[str, float], bool]:
        return project(self.manifold, solution)

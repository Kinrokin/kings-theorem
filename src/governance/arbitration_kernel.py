import time
from typing import Any, Dict, List


class Warrant:
    def __init__(
        self,
        agent_id: str,
        action: str,
        confidence: float,
        ethics_score: float,
        ltl_assertions: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.agent_id = agent_id
        self.action = action
        self.confidence = float(confidence)
        self.ethics_score = float(ethics_score)
        self.ltl_assertions = ltl_assertions or []
        self.metadata = metadata or {}


class QuorumConfig:
    def __init__(self, N: int, K: int, correlation_rho: float = 0.5):
        self.N = int(N)
        self.K = int(K)
        self.correlation_rho = float(correlation_rho)


class Resolution:
    def __init__(self, chosen_warrant: Warrant, reason: str, diagnostics: Dict[str, Any] = None):
        self.chosen_warrant = chosen_warrant
        self.reason = reason
        self.diagnostics = diagnostics or {}


class ArbitrationKernel:
    """Lexicographic Meta-Governor skeleton.

    This is a contract-first stub: it provides the API and basic lexicographic
    resolution rules. Quorum voting and UCB routing are left as pluggable
    implementations.
    """

    def __init__(self):
        self.registry = {}

    def propose_warrant(self, warrant: Warrant) -> str:
        token = f"w_{int(time.time()*1000)}_{len(self.registry)}"
        self.registry[token] = warrant
        return token

    def resolve_conflict(self, tokens: List[str], timeout_ms: int = 800) -> Resolution:
        warrants = [self.registry.get(t) for t in tokens if t in self.registry]
        if not warrants:
            raise ValueError("No warrants to resolve")

        # 1) prioritize by number of LTL assertions
        best = max(warrants, key=lambda w: len(w.ltl_assertions))
        ties = [w for w in warrants if len(w.ltl_assertions) == len(best.ltl_assertions)]
        if len(ties) > 1:
            # 2) prioritize by ethics_score
            best = max(ties, key=lambda w: w.ethics_score)
            ties2 = [w for w in ties if w.ethics_score == best.ethics_score]
            if len(ties2) > 1:
                # 3) fallback: pick by highest confidence
                best = max(ties2, key=lambda w: w.confidence)

        return Resolution(chosen_warrant=best, reason="Lexicographic selection")

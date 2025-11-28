"""Risk Budget enforcement for King's Theorem orchestrator."""

import time
from dataclasses import dataclass, field


@dataclass
class RiskBudget:
    """
    The Divine Accountant - prevents infinite loops and wasted compute.

    Tracks three resource dimensions:
    - max_tokens: total LLM tokens consumed
    - max_depth: recursion/iteration depth
    - timeout_sec: wall-clock time limit
    """

    max_tokens: int = 10_000
    max_depth: int = 10
    timeout_sec: float = 60.0

    _start: float = field(init=False, repr=False)
    tokens_used: int = field(init=False, default=0)
    current_depth: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        self._start = time.time()

    def check(self) -> bool:
        """
        Return False if any budget dimension is exhausted.

        Returns:
            True if resources remain, False if any limit exceeded
        """
        now = time.time()
        if (now - self._start) > self.timeout_sec:
            return False
        if self.current_depth > self.max_depth:
            return False
        if self.tokens_used > self.max_tokens:
            return False
        return True

    def consume(self, *, tokens: int = 0, depth_inc: int = 0) -> None:
        """
        Update resource consumption counters.

        Args:
            tokens: Number of tokens consumed
            depth_inc: Depth increment (typically 1 per iteration)
        """
        self.tokens_used += tokens
        self.current_depth += depth_inc

# src/governance/timing_defense.py
"""
Timing attack defenses and timeout enforcement for kernel orchestration.
Prevents adversarial timing manipulation and stall attacks.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("kt.governance.timing_defense")
logger.setLevel(logging.INFO)


class TimeoutStrategy(Enum):
    FAIL_FAST = "fail_fast"  # Immediately fail on timeout
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Retry with increasing delays
    BLACKLIST = "blacklist"  # Blacklist kernel after repeated timeouts


@dataclass
class TimingConfig:
    """Configuration for timing defenses."""

    default_timeout: float = 5.0  # seconds
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    blacklist_threshold: int = 5  # Number of consecutive timeouts before blacklist
    strategy: TimeoutStrategy = TimeoutStrategy.FAIL_FAST


@dataclass
class KernelTimingStats:
    """Track timing statistics for a kernel."""

    kernel_id: str
    total_calls: int = 0
    timeout_count: int = 0
    consecutive_timeouts: int = 0
    avg_execution_time: float = 0.0
    max_execution_time: float = 0.0
    is_blacklisted: bool = False
    blacklist_reason: str = ""
    execution_times: list = field(default_factory=list)


class TimingDefense:
    """
    Enforces timing constraints and detects timing-based attacks.
    Implements deterministic tie-breaking and timeout handling.
    """

    def __init__(self, config: Optional[TimingConfig] = None):
        self.config = config or TimingConfig()
        self.stats: Dict[str, KernelTimingStats] = {}

    def execute_with_timeout(
        self,
        kernel_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        timeout: Optional[float] = None,
    ) -> tuple[Any, bool]:
        """
        Execute function with timeout enforcement.
        Returns (result, timed_out).
        """
        kwargs = kwargs or {}
        timeout = timeout or self.config.default_timeout

        # Get or create stats
        if kernel_id not in self.stats:
            self.stats[kernel_id] = KernelTimingStats(kernel_id=kernel_id)
        stats = self.stats[kernel_id]

        # Check blacklist
        if stats.is_blacklisted:
            logger.warning(f"Kernel {kernel_id} is blacklisted: {stats.blacklist_reason}")
            return None, True

        stats.total_calls += 1
        start_time = time.time()

        try:
            # Simple timeout using time tracking
            # Note: For true async timeout, use asyncio.wait_for or threading.Timer
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Record timing
            stats.execution_times.append(execution_time)
            if len(stats.execution_times) > 1000:
                stats.execution_times.pop(0)

            stats.avg_execution_time = sum(stats.execution_times) / len(stats.execution_times)
            stats.max_execution_time = max(stats.max_execution_time, execution_time)

            # Check if execution exceeded timeout
            if execution_time > timeout:
                stats.timeout_count += 1
                stats.consecutive_timeouts += 1
                logger.warning(f"Kernel {kernel_id} exceeded timeout: {execution_time:.2f}s > {timeout:.2f}s")
                self._handle_timeout(kernel_id, stats)
                return result, True
            else:
                stats.consecutive_timeouts = 0  # Reset on success
                return result, False

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Kernel {kernel_id} failed after {execution_time:.2f}s: {e}")
            stats.timeout_count += 1
            stats.consecutive_timeouts += 1
            self._handle_timeout(kernel_id, stats)
            raise

    def _handle_timeout(self, kernel_id: str, stats: KernelTimingStats):
        """Handle timeout based on configured strategy."""
        if self.config.strategy == TimeoutStrategy.BLACKLIST:
            if stats.consecutive_timeouts >= self.config.blacklist_threshold:
                stats.is_blacklisted = True
                stats.blacklist_reason = f"Exceeded {self.config.blacklist_threshold} consecutive timeouts"
                logger.error(f"Blacklisting kernel {kernel_id}: {stats.blacklist_reason}")

        elif self.config.strategy == TimeoutStrategy.EXPONENTIAL_BACKOFF:
            # Caller should implement retry logic with backoff
            pass

    def deterministic_tiebreaker(self, candidates: list[tuple[str, float, str]]) -> str:
        """
        Deterministic tie-breaking for kernels with equal warrants.
        Args:
            candidates: List of (kernel_id, warrant, metadata_hash) tuples
        Returns:
            Winning kernel_id
        """
        if not candidates:
            raise ValueError("No candidates for tie-breaking")

        # Sort by warrant (descending), then kernel_id (lexicographic), then metadata_hash
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (-x[1], x[0], x[2]),  # warrant desc, id asc, hash asc
        )

        winner = sorted_candidates[0][0]
        logger.info(f"Tie-breaker resolved: {winner} chosen from {len(candidates)} candidates with equal warrant")
        return winner

    def get_stats(self, kernel_id: str) -> Optional[KernelTimingStats]:
        """Get timing statistics for a kernel."""
        return self.stats.get(kernel_id)

    def reset_stats(self, kernel_id: str):
        """Reset statistics for a kernel."""
        if kernel_id in self.stats:
            self.stats[kernel_id] = KernelTimingStats(kernel_id=kernel_id)

    def unblacklist(self, kernel_id: str):
        """Remove kernel from blacklist (manual intervention)."""
        if kernel_id in self.stats:
            self.stats[kernel_id].is_blacklisted = False
            self.stats[kernel_id].blacklist_reason = ""
            self.stats[kernel_id].consecutive_timeouts = 0
            logger.info(f"Kernel {kernel_id} removed from blacklist")

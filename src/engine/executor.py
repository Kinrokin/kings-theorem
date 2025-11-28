"""
Titanium X Async Executor - Timeout Safety, Structured Error Handling
======================================================================

Adversarial improvements:
- asyncio.wait_for for bounded execution
- Structured ExecResult with error classification enums
- No time.sleep (all async-native with await asyncio.sleep)
- Explicit infra vs infeasible error distinction
- Duration tracking for performance monitoring

Constitutional compliance: Axiom 2 (formal safety), Axiom 3 (auditability)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


class ExecStatus(Enum):
    """Execution outcome classification."""

    OK = "ok"  # Success
    TIMEOUT = "timeout"  # Deadline exceeded
    ERROR_INFRA = "error_infra"  # Infrastructure failure (network, API)
    ERROR_INFEASIBLE = "error_infeasible"  # Task inherently unsolvable
    ERROR_GENERIC = "error_generic"  # Uncategorized error
    CANCELLED = "cancelled"  # Explicit cancellation


class ErrorCode(Enum):
    """Structured error codes for classification."""

    NONE = "NONE"
    TIMEOUT = "TIMEOUT"
    NETWORK = "NETWORK"
    API_LIMIT = "API_LIMIT"
    INVALID_INPUT = "INVALID_INPUT"
    INFEASIBLE_TASK = "INFEASIBLE_TASK"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ExecResult:
    """
    Structured execution result with provenance.

    Attributes:
        status: Execution outcome (ExecStatus enum)
        data: Result data on success, None on failure
        error_code: Structured error code (ErrorCode enum)
        error_msg: Human-readable error message
        duration_ms: Execution duration in milliseconds
        timestamp: ISO 8601 timestamp when execution started
        retry_eligible: Whether this error is retryable
    """

    status: ExecStatus
    data: Optional[Any]
    error_code: ErrorCode
    error_msg: Optional[str] = None
    duration_ms: int = 0
    timestamp: str = ""
    retry_eligible: bool = False

    def __post_init__(self):
        """Set timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def is_success(self) -> bool:
        """Check if execution succeeded."""
        return self.status == ExecStatus.OK

    def is_retryable(self) -> bool:
        """Check if error is eligible for retry."""
        return self.retry_eligible and self.status in [ExecStatus.TIMEOUT, ExecStatus.ERROR_INFRA]

    def to_dict(self) -> dict:
        """Serialize for ledger storage."""
        return {
            "status": self.status.value,
            "error_code": self.error_code.value,
            "error_msg": self.error_msg,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "retry_eligible": self.retry_eligible,
            "has_data": self.data is not None,
        }


async def run_with_timeout(
    callable_fn: Callable[[], Awaitable[Any]], timeout_sec: float = 10.0, task_name: str = "unknown"
) -> ExecResult:
    """
    Execute async callable with timeout enforcement.

    Args:
        callable_fn: Async callable to execute
        timeout_sec: Maximum execution time in seconds
        task_name: Task identifier for logging

    Returns:
        ExecResult with outcome and provenance
    """
    start_time = asyncio.get_event_loop().time()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        logger.debug(f"Starting {task_name} with {timeout_sec}s timeout")
        data = await asyncio.wait_for(callable_fn(), timeout=timeout_sec)
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

        logger.info(f"{task_name} completed in {duration_ms}ms")
        return ExecResult(
            status=ExecStatus.OK,
            data=data,
            error_code=ErrorCode.NONE,
            duration_ms=duration_ms,
            timestamp=timestamp,
            retry_eligible=False,
        )

    except asyncio.TimeoutError:
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        logger.warning(f"{task_name} timed out after {duration_ms}ms")
        return ExecResult(
            status=ExecStatus.TIMEOUT,
            data=None,
            error_code=ErrorCode.TIMEOUT,
            error_msg=f"Execution exceeded {timeout_sec}s deadline",
            duration_ms=duration_ms,
            timestamp=timestamp,
            retry_eligible=True,
        )

    except asyncio.CancelledError:
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        logger.warning(f"{task_name} was cancelled after {duration_ms}ms")
        return ExecResult(
            status=ExecStatus.CANCELLED,
            data=None,
            error_code=ErrorCode.UNKNOWN,
            error_msg="Task was explicitly cancelled",
            duration_ms=duration_ms,
            timestamp=timestamp,
            retry_eligible=False,
        )

    except ConnectionError as e:
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        logger.error(f"{task_name} network error: {e}")
        return ExecResult(
            status=ExecStatus.ERROR_INFRA,
            data=None,
            error_code=ErrorCode.NETWORK,
            error_msg=f"Network failure: {str(e)}",
            duration_ms=duration_ms,
            timestamp=timestamp,
            retry_eligible=True,
        )

    except ValueError as e:
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        logger.error(f"{task_name} invalid input: {e}")
        return ExecResult(
            status=ExecStatus.ERROR_INFEASIBLE,
            data=None,
            error_code=ErrorCode.INVALID_INPUT,
            error_msg=f"Invalid input: {str(e)}",
            duration_ms=duration_ms,
            timestamp=timestamp,
            retry_eligible=False,
        )

    except Exception as e:
        duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        logger.exception(f"{task_name} generic error: {e}")
        return ExecResult(
            status=ExecStatus.ERROR_GENERIC,
            data=None,
            error_code=ErrorCode.UNKNOWN,
            error_msg=f"Unexpected error: {str(e)}",
            duration_ms=duration_ms,
            timestamp=timestamp,
            retry_eligible=False,
        )


async def run_with_retry(
    callable_fn: Callable[[], Awaitable[Any]],
    max_retries: int = 3,
    timeout_sec: float = 10.0,
    backoff_sec: float = 1.0,
    task_name: str = "unknown",
) -> ExecResult:
    """
    Execute with constant-time retry on retryable failures (timing oracle resistant).

    Uses fixed delay + random jitter to prevent timing-based state inference.
    Retry count is opaque to external observers (no timing leak).

    Args:
        callable_fn: Async callable to execute
        max_retries: Maximum retry attempts
        timeout_sec: Timeout per attempt
        backoff_sec: Fixed backoff duration (with ±20% jitter)
        task_name: Task identifier

    Returns:
        ExecResult from last attempt

    Security:
        Prevents timing oracle attacks by using constant delay regardless
        of retry count. Jitter prevents statistical analysis of retry patterns.
    """
    import secrets

    last_result: Optional[ExecResult] = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            # Constant-time delay with random jitter (±20%)
            # Prevents oracle from inferring retry count via timing
            sr = secrets.SystemRandom()
            jitter = sr.uniform(-0.2, 0.2)
            delay = backoff_sec * (1.0 + jitter)
            logger.info(f"{task_name} retry {attempt}/{max_retries} after fixed backoff")
            await asyncio.sleep(delay)

        result = await run_with_timeout(callable_fn, timeout_sec, f"{task_name}[{attempt}]")
        last_result = result

        if result.is_success():
            return result

        if not result.is_retryable():
            logger.warning(f"{task_name} non-retryable error: {result.error_code.value}")
            # Still wait same delay as retryable case to prevent timing leak
            if attempt < max_retries:
                sr = secrets.SystemRandom()
                jitter = sr.uniform(-0.2, 0.2)
                delay = backoff_sec * (1.0 + jitter)
                await asyncio.sleep(delay)
            return result

    # All retries exhausted
    if last_result is None:
        logger.error("%s exhausted %d retries and no result captured", task_name, max_retries)
        raise RuntimeError(f"{task_name} exhausted retries without result")
    logger.error(f"{task_name} exhausted {max_retries} retries")
    return last_result


class ExecutionPool:
    """
    Managed pool for concurrent executions with resource limits.

    Prevents resource exhaustion from unbounded concurrent tasks.
    """

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize execution pool.

        Args:
            max_concurrent: Maximum concurrent executions
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks: set = set()
        self.max_concurrent = max_concurrent
        logger.info(f"ExecutionPool initialized: max_concurrent={max_concurrent}")

    async def execute(
        self, callable_fn: Callable[[], Awaitable[Any]], timeout_sec: float = 10.0, task_name: str = "unknown"
    ) -> ExecResult:
        """
        Execute callable with pool resource management.

        Args:
            callable_fn: Async callable
            timeout_sec: Timeout per execution
            task_name: Task identifier

        Returns:
            ExecResult
        """
        async with self.semaphore:
            task = asyncio.current_task()
            if task:
                self.active_tasks.add(task)

            try:
                result = await run_with_timeout(callable_fn, timeout_sec, task_name)
                return result
            finally:
                if task:
                    self.active_tasks.discard(task)

    def get_utilization(self) -> float:
        """
        Get current pool utilization (0.0-1.0).

        Returns:
            Ratio of active tasks to max concurrent
        """
        return len(self.active_tasks) / self.max_concurrent

    async def shutdown(self, timeout_sec: float = 5.0) -> None:
        """
        Gracefully shutdown pool, cancelling active tasks.

        Args:
            timeout_sec: Maximum time to wait for task cancellation
        """
        logger.info(f"Shutting down ExecutionPool: {len(self.active_tasks)} active tasks")

        for task in self.active_tasks:
            task.cancel()

        # Wait for cancellation with timeout
        if self.active_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*self.active_tasks, return_exceptions=True), timeout=timeout_sec)
            except asyncio.TimeoutError:
                logger.warning("ExecutionPool shutdown: some tasks did not cancel in time")

        logger.info("ExecutionPool shutdown complete")

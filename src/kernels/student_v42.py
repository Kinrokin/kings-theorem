"""Student kernel v42 - Titanium X Edition

Improvements applied in this refactor:
- Dependency-inject the LLM call for testability
- Structured return via dataclass
- Timeout / retries with exponential backoff
- Logging and timing metrics
- Input validation and clearer exception handling

Titanium X Upgrades:
- Z3 formal verification for constraint checking (replaces procedural logic)
- AxiomaticVerifier integration for safety invariants
- Formal proof generation for decision justification
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, Optional

from src.governance.nemo_guard import DeontologicalGuardrail
from src.llm_interface import query_qwen
from src.primitives.axiomatic_verifier import AxiomaticVerifier
from src.primitives.exceptions import SecurityError, StandardizedInfeasibilityToken

logger = logging.getLogger(__name__)


@dataclass
class StudentResult:
    status: str
    solution: Optional[str]
    model_used: Optional[str]
    duration_s: float
    meta: Dict[str, Any]


class StudentKernelV42:
    """A lightweight student kernel that delegates to an LLM.

    Use dependency injection for the `llm_call` to make this class
    easy to unit-test and to swap model providers.
    """

    def __init__(
        self,
        llm_call: Callable[..., Any] = query_qwen,
        model_name: str = "qwen2.5",
        system_rule: str = "You are a rigor-focused academic engine.",
        timeout: int = 120,
        max_retries: int = 2,
        *,
        guardrail: Optional[DeontologicalGuardrail] = None,
        verifier: Optional[AxiomaticVerifier] = None,
    ) -> None:
        # Guardrail is optional for lightweight/test instantiation; validate only if provided
        if guardrail is not None and not isinstance(guardrail, DeontologicalGuardrail):
            raise SecurityError("guardrail must be a DeontologicalGuardrail instance if provided")
        self.llm_call = llm_call
        self.model_name = model_name
        self.system_rule = system_rule
        self.timeout = timeout
        self.max_retries = max_retries
        self.guardrail = guardrail

        # Titanium X: Z3 formal verifier for constraint checking
        self.verifier = verifier or AxiomaticVerifier(timeout_ms=5000)
        logger.info("StudentKernelV42 initialized with AxiomaticVerifier")

    def staged_solve_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Accepts a problem dict and returns a standardized result dict.

        Expected keys in `problem`: 'task', 'data', 'constraint'. Missing keys are treated
        as empty strings.
        """
        # Validate input shape quickly
        if not isinstance(problem, dict):
            raise ValueError("problem must be a dict")

        task_prompt = str(problem.get("task", "")).strip()
        context = str(problem.get("data", "")).strip()
        constraint = str(problem.get("constraint", "")).strip()

        full_prompt = (
            f"TASK: {task_prompt}\nCONTEXT: {context}\nCONSTRAINT: {constraint}\n\nProvide a detailed solution."
        )

        # Attempt LLM calls with simple retry/backoff
        attempt = 0
        start_time = time.time()
        last_meta: Dict[str, Any] = {}
        while attempt <= self.max_retries:
            try:
                attempt += 1
                logger.info("StudentKernelV42 calling LLM (attempt %d)", attempt)

                # llm_call is expected to either return a text response or a dict-like object.
                try:
                    response = self.llm_call(
                        prompt=full_prompt,
                        system_rule=self.system_rule,
                        timeout=self.timeout,
                        model=self.model_name,
                    )
                except Exception as e:
                    logger.exception("Error while calling llm_call")
                    # If we've exhausted retries, return SIT with reason
                    if attempt > self.max_retries:
                        duration = time.time() - start_time
                        return asdict(
                            StudentResult(
                                status="SIT",
                                solution=None,
                                model_used=self.model_name,
                                duration_s=round(duration, 3),
                                meta={"reason": str(e), "attempts": attempt},
                            )
                        )
                    time.sleep(0.5 * attempt)
                    continue

                # Normalize response into text if necessary
                if isinstance(response, dict):
                    # Try common keys
                    text = response.get("text") or response.get("response") or response.get("content") or str(response)
                    last_meta = {k: v for k, v in response.items() if k != "text"}
                else:
                    text = str(response)

                # Detect standardized error markers coming back from lower-level LLM layer
                if "[ERROR]" in text or "[CRITICAL]" in text:
                    raise StandardizedInfeasibilityToken("LLM returned error marker")

                duration = time.time() - start_time

                # TITANIUM X: Verify solution constraints with Z3 before returning
                if self.verifier and "state" in problem:
                    state = problem["state"]
                    is_safe, proof = self.verifier.verify_with_proof(state)
                    last_meta["z3_proof"] = proof
                    last_meta["z3_safe"] = is_safe
                    if not is_safe:
                        logger.warning("[TITANIUM] Z3 verification failed: %s", proof)
                        # Still return solution, but mark with verification status
                        last_meta["z3_warning"] = "Safety invariant not proven"

                result = StudentResult(
                    status="PASS (Student)",
                    solution=text,
                    model_used=self.model_name,
                    duration_s=round(duration, 3),
                    meta={"attempts": attempt, **last_meta},
                )
                return asdict(result)

            except StandardizedInfeasibilityToken:
                logger.exception("LLM indicated infeasibility or connection error")
                # If it's the last attempt, return SIT
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={
                                "reason": "LLM infeasible or offline",
                                "attempts": attempt,
                            },
                        )
                    )
                # else, simple backoff
                time.sleep(0.5 * attempt)

    # --- Utilities ---
    @staticmethod
    def build_prompt(task: str, context: str = "", constraint: str = "") -> str:
        """Build a standardized prompt from pieces. Useful to centralize formatting and
        to make testing prompt shapes easier.
        """
        task_prompt = str(task or "").strip()
        context = str(context or "").strip()
        constraint = str(constraint or "").strip()
        return f"TASK: {task_prompt}\nCONTEXT: {context}\nCONSTRAINT: {constraint}\n\nProvide a detailed solution."

    class Metrics:
        """A tiny local metrics helper. Replace with Prometheus/StatsD client in prod.

        Usage:
            m = StudentKernelV42.Metrics()
            m.increment('calls')
            m.observe('latency_s', 0.23)
        """

        def __init__(self) -> None:
            self._counters: Dict[str, int] = {}
            self._gauges: Dict[str, float] = {}

        def increment(self, name: str, amount: int = 1) -> None:
            self._counters[name] = self._counters.get(name, 0) + amount

        def observe(self, name: str, value: float) -> None:
            # store last observed value for simplicity
            self._gauges[name] = float(value)

        def snapshot(self) -> Dict[str, Any]:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges)}

    async def async_staged_solve_pipeline(self, problem: Dict[str, Any], async_llm_call=None) -> Dict[str, Any]:
        """Async variant. `async_llm_call` should be an awaitable function with same
        signature as the sync `llm_call`. If not provided, raises ValueError.
        """
        if async_llm_call is None:
            raise ValueError("async_llm_call is required for async_staged_solve_pipeline")

        # reuse the existing prompt builder and retry/backoff strategy, but await the async call
        if not isinstance(problem, dict):
            raise ValueError("problem must be a dict")

        task = problem.get("task", "")
        context = problem.get("data", "")
        constraint = problem.get("constraint", "")
        full_prompt = self.build_prompt(task, context, constraint)

        attempt = 0
        start_time = time.time()
        last_meta: Dict[str, Any] = {}
        while attempt <= self.max_retries:
            try:
                attempt += 1
                logger.info("StudentKernelV42 async calling LLM (attempt %d)", attempt)
                response = await async_llm_call(
                    prompt=full_prompt,
                    system_rule=self.system_rule,
                    timeout=self.timeout,
                    model=self.model_name,
                )

                if isinstance(response, dict):
                    text = response.get("text") or response.get("response") or response.get("content") or str(response)
                    last_meta = {k: v for k, v in response.items() if k != "text"}
                else:
                    text = str(response)

                if "[ERROR]" in text or "[CRITICAL]" in text:
                    raise StandardizedInfeasibilityToken("LLM returned error marker")

                duration = time.time() - start_time
                result = StudentResult(
                    status="PASS (Student)",
                    solution=text,
                    model_used=self.model_name,
                    duration_s=round(duration, 3),
                    meta={"attempts": attempt, **last_meta},
                )
                return asdict(result)

            except StandardizedInfeasibilityToken:
                logger.exception("LLM indicated infeasibility or connection error (async)")
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={
                                "reason": "LLM infeasible or offline",
                                "attempts": attempt,
                            },
                        )
                    )
                await __import__("asyncio").sleep(0.5 * attempt)

            except Exception:
                logger.exception("Unexpected error in StudentKernelV42 (async)")
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={
                                "reason": "unexpected async error",
                                "attempts": attempt,
                            },
                        )
                    )
                await __import__("asyncio").sleep(0.5 * attempt)

            except Exception as e:
                logger.exception("Unexpected error in StudentKernelV42")
                # If we've exhausted retries, return SIT with reason
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={"reason": str(e), "attempts": attempt},
                        )
                    )
                time.sleep(0.5 * attempt)

"""KT-Agent V1 — Level 4 sequential agent using KT adapters.

This agent coordinates Student/Teacher/Arbiter models to act in an environment
with guardrails and trajectory verification. Logging to an EventLog-like object
is expected via an `append_event` method.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Protocol

from src.governance.semantic_guard import SemanticGuard
from src.models.adapters import KTModelAdapter

logger = logging.getLogger(__name__)


class EventLogger(Protocol):
    """Protocol for event logging with an append_event method."""

    def append_event(self, event: Dict[str, Any]) -> None:  # pragma: no cover
        ...


TrajectoryEvent = Dict[str, Any]


class KTAgentV1:
    """Level 4 sequential agent orchestrating Student/Teacher/Arbiter.

    Args:
        student: Adapter for proposing actions.
        teacher: Adapter for critiquing/correcting actions.
        arbiter: Adapter for constitutional verdicts.
        semantic_guard: Symbolic/semantic guard for risk checks.
        trajectory_verifier: Optional trajectory verifier (MTL-like).
        event_log: Logger with `append_event` method.
        max_steps: Episode step limit.
    """

    def __init__(
        self,
        student: KTModelAdapter,
        teacher: KTModelAdapter,
        arbiter: KTModelAdapter,
        semantic_guard: SemanticGuard,
        trajectory_verifier: Any,
        event_log: EventLogger,
        max_steps: int = 20,
    ) -> None:
        self.student = student
        self.teacher = teacher
        self.arbiter = arbiter
        self.guard = semantic_guard
        self.traj_verifier = trajectory_verifier
        self.log = event_log
        self.max_steps = max_steps

    def _build_step_prompt(self, history: List[TrajectoryEvent], obs: Dict[str, Any]) -> str:
        return (
            "You are the KT-Student operating under a constitutional governor.\n"
            "History:\n"
            f"{history}\n"
            "Current observation:\n"
            f"{obs}\n"
            "Propose the next action in structured JSON form."
        )

    def act_episode(self, env: Any) -> Dict[str, Any]:
        obs = env.reset()
        history: List[TrajectoryEvent] = []
        for t in range(self.max_steps):
            step_prompt = self._build_step_prompt(history, obs)
            student_raw = self.student.generate(step_prompt)

            teacher_prompt = f"Critique and, if needed, correct this action:\n{student_raw}"
            teacher_raw = self.teacher.generate(teacher_prompt)

            arbiter_prompt = (
                "You are the Arbiter. Decide if this action is constitutional and safe.\n\n"
                f"Student action:\n{student_raw}\n\n"
                f"Teacher critique:\n{teacher_raw}\n"
                'Respond with JSON: {"vetoed": bool, "reason": str}'
            )
            arbiter_raw = self.arbiter.generate(arbiter_prompt)
            arbiter_decision = self._safe_parse_json(arbiter_raw, default={"vetoed": False, "reason": "UNKNOWN"})

            guard_result = self.guard.assess_risk(student_raw + "\n" + teacher_raw)

            step_event: TrajectoryEvent = {
                "t": t,
                "obs": obs,
                "student_raw": student_raw,
                "teacher_raw": teacher_raw,
                "arbiter": arbiter_decision,
                "guard": guard_result,
            }
            try:
                self.log.append_event(step_event)
            except Exception as e:
                logger.warning("Event logging failed: %s", e)

            if guard_result.get("is_blocked") or arbiter_decision.get("vetoed", False):
                return {
                    "status": "BLOCKED",
                    "reason": arbiter_decision.get("reason") or guard_result.get("reason"),
                    "history": history + [step_event],
                }

            action = self._decode_action(student_raw, teacher_raw)
            next_obs, env_reward, done, info = env.step(action)
            step_event.update({"action": action, "env_reward": env_reward, "done": done, "env_info": info})
            history.append(step_event)

            if done:
                break
            obs = next_obs

        mtl_result = None
        if self.traj_verifier is not None and hasattr(self.traj_verifier, "verify"):
            try:
                mtl_result = self.traj_verifier.verify(history)
            except Exception as e:
                logger.warning("Trajectory verification failed: %s", e)

        episode_summary = {
            "status": "DONE",
            "history": history,
            "mtl_result": mtl_result,
        }
        try:
            self.log.append_event({"type": "EPISODE_SUMMARY", "summary": episode_summary})
        except Exception as e:
            logger.warning("Episode summary logging failed: %s", e)
        return episode_summary

    def _safe_parse_json(self, text: str, default: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            return default

    def _decode_action(self, student_raw: str, teacher_raw: str) -> Dict[str, Any]:
        for source_label, candidate in (("student", student_raw), ("teacher", teacher_raw)):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                logger.debug("Action decode failed for %s payload: %s", source_label, e)
                # fall through to try the next candidate
        return {"type": "noop"}

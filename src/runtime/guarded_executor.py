"""Guarded Runtime Executor — KT constitutional sandbox (Level 5).

All actions are passed through councils, guardrails, MTL evaluation, and the
ParadoxHarmonizer before being executed.
"""

from __future__ import annotations

from typing import Any, Dict

from src.governance.paradox_harmonizer import ParadoxHarmonizer
from src.governance.semantic_guard import SemanticGuard
from src.runtime.tools import ToolRegistry, tool_math
from src.trinity.society import ArbiterCouncil, StudentCouncil, TeacherCouncil


class KTGuardedExecutor:
    """Runtime cage that enforces constitutional governance on actions."""

    def __init__(
        self,
        students: StudentCouncil,
        teachers: TeacherCouncil,
        arbiters: ArbiterCouncil,
        semantic_guard: SemanticGuard,
        mtl_engine: Any,
        harmonizer: ParadoxHarmonizer,
        event_log: Any,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.students = students
        self.teachers = teachers
        self.arbiters = arbiters
        self.guard = semantic_guard
        self.mtl = mtl_engine
        self.harmonizer = harmonizer
        self.log = event_log
        self.tools = tool_registry or ToolRegistry()
        self.tools.register("math", tool_math)

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Govern and execute a runtime request.

        Expected request shape:
            {
                "actor": "agent|tool|external",
                "intent": "call_tool|write_file|send_message|execute_code|modify_memory|echo",
                "payload": {...},
                "context": {...}
            }
        """

        prompt = self._build_governance_prompt(request)
        proposals = self.students.propose(prompt)
        teacher_evals = self.teachers.evaluate(prompt, proposals)
        arbiter_view = self.arbiters.decide(prompt, proposals, teacher_evals)

        guard_payload_str = str(request) + str(proposals) + str(teacher_evals)
        guard_result = self._guard_assess(guard_payload_str)

        mtl_results = []
        if self.mtl is not None and hasattr(self.mtl, "evaluate_runtime"):
            mtl_results = self.mtl.evaluate_runtime(request, proposals, teacher_evals, arbiter_view, guard_result)

        harmonized = self.harmonizer.harmonize(mtl_results)

        self.log.append_event(
            {
                "type": "RUNTIME_REVIEW",
                "request": request,
                "proposals": proposals,
                "teacher_evals": teacher_evals,
                "arbiter_view": arbiter_view,
                "guard_result": guard_result,
                "mtl_results": mtl_results,
                "harmonized": harmonized,
            }
        )

        if guard_result.get("is_blocked") or arbiter_view.get("vetoed") or harmonized.get("decision") == "VETO":
            return {
                "status": "DENIED",
                "reason": "CONSTITUTIONAL_VETO",
                "details": {
                    "arbiter": arbiter_view,
                    "guard": guard_result,
                    "harmonized": harmonized,
                },
            }

        result = self._perform(request)
        self.log.append_event({"type": "RUNTIME_ACTION_EXECUTED", "request": request, "result": result})
        return {"status": "OK", "result": result}

    def _build_governance_prompt(self, request: Dict[str, Any]) -> str:
        return (
            "You are part of the KT governance council.\n"
            "Assess the following action request under constitutional rules:\n\n"
            f"{request}\n"
        )

    def _perform(self, request: Dict[str, Any]) -> Any:
        intent = request.get("intent")
        payload = request.get("payload", {})
        if intent == "echo":
            return {"echo": payload}
        if intent == "tool_call":
            tool_name = payload.get("tool")
            args = payload.get("args", {})
            tool = self.tools.get(tool_name)
            if tool is None:
                return {"error": f"Tool '{tool_name}' not found"}
            try:
                return {"tool": tool_name, "output": tool(args)}
            except Exception as e:
                return {"error": f"Tool execution failed: {e}"}
        # TODO: add safe tool integrations here
        return {"noop": True}

    def _guard_assess(self, text: str) -> Dict[str, Any]:
        """Adapt to available SemanticGuard API.

        Tries `assess_risk`, then `assess`, then `validate_content` style returning
        a normalized dict: {"is_blocked": bool, "reason": str} plus any extras.
        """
        guard = self.guard
        # Prefer assess_risk
        fn = getattr(guard, "assess_risk", None)
        if callable(fn):
            res = fn(text)
            if isinstance(res, dict):
                return res
            is_blocked = getattr(res, "is_blocked", False)
            reason = getattr(res, "reason", "UNKNOWN")
            return {"is_blocked": bool(is_blocked), "reason": str(reason)}
        # Fallback to assess
        fn = getattr(guard, "assess", None)
        if callable(fn):
            res = fn(text)
            if isinstance(res, dict):
                return res
            is_blocked = getattr(res, "is_blocked", False)
            reason = getattr(res, "reason", "UNKNOWN")
            return {"is_blocked": bool(is_blocked), "reason": str(reason)}
        # Fallback to validate_content(text) -> (bool, reason)
        fn = getattr(guard, "validate_content", None)
        if callable(fn):
            try:
                allowed, reason = fn(text)
                return {"is_blocked": not bool(allowed), "reason": reason}
            except Exception:
                return {"is_blocked": False, "reason": "UNKNOWN"}
        # Default permissive
        return {"is_blocked": False, "reason": "NO_GUARD_API"}

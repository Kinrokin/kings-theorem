"""Shared helpers for Phase 4 integration tests."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def configure_stub_student(monkeypatch) -> None:
    """Stub the student kernel to avoid external LLM calls during tests."""

    def _fake_staged_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        task = str(problem.get("task", ""))
        return {
            "status": "PASS (Student)",
            "solution": f"Stubbed resolution for {task or 'unspecified task'}",
            "model_used": "stubbed-llm",
            "duration_s": 0.01,
            "meta": {"stub": True},
        }

    monkeypatch.setattr(
        "src.kernels.student_v42.StudentKernelV42.staged_solve_pipeline",
        _fake_staged_pipeline,
    )


def build_problem_graph(
    task: str,
    *,
    constraint: str = "Uphold governance directives and protect civilians",
    tags: Optional[Iterable[str]] = None,
    action_type: str = "BENIGN_ACTION",
    utility: float = 1.0,
) -> Dict[str, Any]:
    """Construct a canonical problem graph used across integration tests."""

    return {
        "task": task,
        "constraint": constraint,
        "metadata": {"domain": "integration", "tags": list(tags or [])},
        "proposed_actions": [
            {
                "type": action_type,
                "utility": utility,
                "summary": task[:120],
            }
        ],
        "module3_planning": {"constraints": {"E_peak_threshold": 60}},
        "data": {"context": task},
    }

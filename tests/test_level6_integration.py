from typing import Any, Dict

import pytest

from src.config.loader import load_constitution
from src.governance.paradox_harmonizer import ParadoxHarmonizer
from src.models.adapters import KTModelAdapter
from src.runtime.guarded_executor import KTGuardedExecutor
from src.trinity.society import ArbiterCouncil, StudentCouncil, TeacherCouncil


# --- Local Stubs (avoid modifying repo for test-only needs) ---
class MTLEngineStub:
    def evaluate_runtime(
        self,
        request: Dict[str, Any],
        proposals: Any,
        teacher_evals: Any,
        arbiter_view: Dict[str, Any],
        guard_result: Dict[str, Any],
    ) -> list[dict]:
        # Minimal: all satisfied to allow harmonizer to aggregate
        return [
            {"spec": "risk_bounded", "result": "SATISFIED"},
            {"spec": "plan_coherent", "result": "SATISFIED"},
        ]


class SimpleEventLog:
    def __init__(self, backend: Any) -> None:
        self.backend = backend

    def append_event(self, event: Dict[str, Any]) -> None:
        self.backend.append_event(event)


class MockBackend:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append_event(self, e: Dict[str, Any]) -> None:
        self.events.append(e)


class AutoApproveAdapter(KTModelAdapter):
    def __init__(self) -> None:
        super().__init__("mock", {})

    def generate(self, p: str, **k: Any) -> str:
        return '{"vetoed": false, "reason": "OK"}'


def test_full_constitutional_tool_execution():
    constitution = load_constitution("config/constitution.yml")
    assert "no_data_exfiltration" in constitution["specs"]

    harmonizer = ParadoxHarmonizer(constitution)
    mtl = MTLEngineStub()

    class PermissiveGuard:
        def assess(self, text: str):
            return {"is_blocked": False, "reason": "OK"}

    guard = PermissiveGuard()

    adapter = AutoApproveAdapter()
    students = StudentCouncil([adapter])
    teachers = TeacherCouncil([adapter])
    arbiters = ArbiterCouncil([adapter])

    backend = MockBackend()
    ledger = SimpleEventLog(backend)

    executor = KTGuardedExecutor(
        students=students,
        teachers=teachers,
        arbiters=arbiters,
        semantic_guard=guard,
        mtl_engine=mtl,
        harmonizer=harmonizer,
        event_log=ledger,
    )

    req_safe = {
        "actor": "user",
        "intent": "tool_call",
        "payload": {"tool": "math", "args": {"expr": "10 * 5"}},
    }

    res = executor.execute(req_safe)
    assert res["status"] == "OK"
    assert res["result"]["output"]["result"] == 50

    review_event = next(e for e in backend.events if e["type"] == "RUNTIME_REVIEW")
    assert review_event["harmonized"]["decision"] == "ALLOW"

    print("\n[SUCCESS] Level 6 Circuit: YAML Law -> Harmonizer -> Executor -> Tool -> Ledger")


if __name__ == "__main__":
    pytest.main([__file__, "-q"])

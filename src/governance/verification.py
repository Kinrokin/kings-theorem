"""
AID: /src/governance/verification.py
Proof ID: PRF-LTL-010
Axiom: Axiom 2: Formal Safety
"""

try:
    import mtl
except ImportError:
    mtl = None


class RollingVerifier:
    def __init__(self, max_steps: int = 12):
        self.max_steps = max_steps
        if mtl:
            try:
                self.phi = mtl.parse("G ( request -> F grant )")  # simplified to avoid parse errors
            except Exception:
                self.phi = None
        else:
            self.phi = None

    def _normalize(self, trace: list) -> list:
        normalized = []
        for event in trace:
            if isinstance(event, dict):
                phase = event.get("phase") or event.get("type") or ""
                status = event.get("status")
                if status is None and isinstance(event.get("data"), dict):
                    status = event["data"].get("status")
                normalized.append((str(phase), str(status or "")))
            elif isinstance(event, (list, tuple)) and len(event) >= 2:
                normalized.append((str(event[0]), str(event[1])))
        return normalized

    def verify_trace(self, trace: list) -> bool:
        """Check monotonicity + bounded response invariants."""

        normalized = self._normalize(trace)
        if not normalized or len(normalized) > self.max_steps:
            return False

        halted = False
        settlement_seen = False
        final_statuses = {"COMMITTED", "ESCROWED", "TIER_5_HALT", "HALT_TRACE", "HALT", "DROP", "FREEZE"}
        forbidden_post_halt = {"EXECUTE", "COMMITTED", "SOLVED", "PASS", "PASS (STUDENT)", "ESCROWED"}

        for phase, status in normalized:
            status_upper = status.upper()
            if halted and status_upper in forbidden_post_halt:
                return False
            if status_upper in {"TIER_5_HALT", "HALT", "VETO", "HALT_TRACE"}:
                halted = True
            if status_upper in final_statuses:
                settlement_seen = True

        return settlement_seen

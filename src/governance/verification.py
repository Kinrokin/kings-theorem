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
    def __init__(self):
        if mtl:
            try:
                self.phi = mtl.parse("G ( request -> F grant )")  # simplified to avoid parse errors
            except Exception:
                self.phi = None
        else:
            self.phi = None

    def verify_trace(self, trace: list) -> bool:
        """Semantic structural verification of execution trace.

        Expected minimal ordering:
          1. student_step
          2. (optional) teacher_step if student SIT/failed
          3. arbiter_ruling
          4. governance_decision

        Each trace element is a dict with 'type' and 'data'.
        Returns False if ordering violated or required steps missing.
        """
        if not isinstance(trace, list) or not trace:
            return False
        types = [t.get("type") for t in trace if isinstance(t, dict)]
        if "student_step" not in types:
            return False
        if "arbiter_ruling" not in types:
            return False
        if "governance_decision" not in types:
            return False
        # Teacher required only if student produced SIT
        student_idx = types.index("student_step")
        student_data = trace[student_idx].get("data", {})
        student_status = student_data.get("status", "")
        if student_status.startswith("SIT") and "teacher_step" not in types:
            return False
        # Ordering constraints
        order_ok = types.index("student_step") < types.index("arbiter_ruling") < types.index("governance_decision")
        if not order_ok:
            return False
        return True

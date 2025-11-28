from src.governance.verification import RollingVerifier


def test_verifier_accepts_monotonic_trace():
    verifier = RollingVerifier()
    trace = [
        ("STUDENT", "PASS"),
        ("GUARDRAIL", "PASS"),
        ("TRIGOVERNOR", "EXECUTE"),
        ("BROKER", "COMMITTED"),
    ]
    assert verifier.verify_trace(trace)


def test_verifier_rejects_grant_after_halt():
    verifier = RollingVerifier()
    trace = [
        ("STUDENT", "PASS"),
        ("GUARDRAIL", "VETO"),
        ("TRIGOVERNOR", "HALT"),
        ("BROKER", "COMMITTED"),
    ]
    assert not verifier.verify_trace(trace)

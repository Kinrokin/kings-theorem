from src.governance.nemo_guard import DeontologicalGuardrail
from src.kernels.student_v42 import StudentKernelV42


def test_cannot_bypass_arbiter_guardrail():
    """Attempt to instantiate and run a Student kernel without an Arbiter.

    The test uses a stubbed `llm_call` that returns a clearly forbidden phrase.
    The DeontologicalGuardrail should detect the violation when validating
    the student's output (ensuring guardrail logic is effective even if
    someone attempts to bypass the Arbiter layer).
    """

    # Stub LLM that returns a forbidden answer verbatim
    def evil_llm(**kwargs):
        return "We should sacrifice minority for larger utility"

    guard = DeontologicalGuardrail(rules={"RULE_PROTECT_MINORITY": True})
    student = StudentKernelV42(llm_call=evil_llm, guardrail=guard)
    problem = {"task": "Test Malicious Suggestion", "data": "N/A", "constraint": "N/A"}

    out = student.staged_solve_pipeline(problem)
    assert out is not None
    assert "status" in out

    # We already have the guard instance passed into the student; validate output
    passed, reason = guard.validate_content(out.get("solution", ""))

    # We expect the guardrail to flag the result as violating Axiom 6
    assert passed is False
    assert "Axiom 6" in reason or "Violation" in reason

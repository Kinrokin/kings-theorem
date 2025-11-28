"""
Test proof DSL cycle detection and spoofing prevention.
"""


def test_proof_spoofing_cycle():
    """Test that circular proofs are detected and rejected."""
    from src.proofs.proof_lang import ProofChecker, ProofObject, ProofStatus, ProofStep

    # Construct a cyclic proof: s1 depends on s2, s2 depends on s1
    step1 = ProofStep(step_id="s1", rule="ASSUME", premises=["s2"], conclusion="p")
    step2 = ProofStep(step_id="s2", rule="ASSUME", premises=["s1"], conclusion="q")
    proof = ProofObject(
        proposition="p",
        steps=[step1, step2],
        required_invariants=set(),
        claimed_satisfactions={},
    )

    checker = ProofChecker()
    status = checker.check_proof(proof)
    assert status == ProofStatus.CONTRADICTORY, "Cyclic proof should be marked CONTRADICTORY"


def test_proof_missing_premise():
    """Test that proofs with missing premises are rejected."""
    from src.proofs.proof_lang import ProofChecker, ProofObject, ProofStatus, ProofStep

    # Step references non-existent premise
    step1 = ProofStep(step_id="s1", rule="ASSUME", premises=["s_nonexistent"], conclusion="p")
    proof = ProofObject(
        proposition="p",
        steps=[step1],
        required_invariants=set(),
        claimed_satisfactions={},
    )

    checker = ProofChecker()
    status = checker.check_proof(proof)
    assert status == ProofStatus.REFUTED, "Proof with missing premise should be REFUTED"


def test_proof_valid_simple():
    """Test that valid simple proofs are accepted."""
    from src.proofs.proof_lang import ProofChecker, ProofObject, ProofStatus, ProofStep

    # Valid proof: s1 is assumption, s2 derives from s1
    proof = ProofObject(
        proposition="q",
        assumptions={"s1"},
        steps=[
            ProofStep(step_id="s1", rule="ASSUME", premises=[], conclusion="p"),
            ProofStep(step_id="s2", rule="AND_INTRO", premises=["s1"], conclusion="q"),
        ],
        required_invariants=set(),
        claimed_satisfactions={},
    )

    checker = ProofChecker()
    status = checker.check_proof(proof)
    assert status == ProofStatus.PROVEN, "Valid proof should be PROVEN"


def test_proof_invariant_violation():
    """Test that false invariant claims are detected."""
    from src.proofs.proof_lang import ConstraintRef, ProofChecker, ProofObject, ProofStatus

    # Constraint that will fail verification
    def bad_verifier(cref):
        return False  # Always fail

    cref = ConstraintRef(id="c1", expression="x > 0")
    proof = ProofObject(
        proposition="x_positive",
        assumptions=set(),
        steps=[],
        required_invariants={cref},
        claimed_satisfactions={"c1": True},  # Claim it's satisfied
    )

    checker = ProofChecker(constraint_verifier=bad_verifier)
    status = checker.check_proof(proof)
    assert status == ProofStatus.REFUTED, "Proof with false invariant should be REFUTED"


def test_proof_pending_invariant():
    """Test that unclaimed invariants keep proof pending."""
    from src.proofs.proof_lang import ConstraintRef, ProofChecker, ProofObject, ProofStatus

    cref = ConstraintRef(id="c1", expression="x > 0")
    proof = ProofObject(
        proposition="x_positive",
        assumptions=set(),
        steps=[],
        required_invariants={cref},
        claimed_satisfactions={},  # Not claimed
    )

    checker = ProofChecker()
    status = checker.check_proof(proof)
    assert status == ProofStatus.PENDING, "Proof with unclaimed invariant should be PENDING"


def test_proof_complex_dag():
    """Test valid DAG proof structure."""
    from src.proofs.proof_lang import ProofChecker, ProofObject, ProofStatus, ProofStep

    # Valid DAG: s1, s2 are assumptions, s3 depends on both
    proof = ProofObject(
        proposition="r",
        assumptions={"s1", "s2"},
        steps=[
            ProofStep(step_id="s1", rule="ASSUME", premises=[], conclusion="p"),
            ProofStep(step_id="s2", rule="ASSUME", premises=[], conclusion="q"),
            ProofStep(step_id="s3", rule="AND_INTRO", premises=["s1", "s2"], conclusion="r"),
        ],
        required_invariants=set(),
        claimed_satisfactions={},
    )

    checker = ProofChecker()
    status = checker.check_proof(proof)
    assert status == ProofStatus.PROVEN, "Valid DAG proof should be PROVEN"

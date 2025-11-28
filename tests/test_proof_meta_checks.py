# tests/test_proof_meta_checks.py
from src.proofs.proof_lang import ConstraintRef, ProofChecker, ProofObject, ProofStatus, ProofStep


def test_proof_cycle_detection():
    """Test that circular proof dependencies are rejected."""
    proof = ProofObject(proposition="A -> B")

    # Create circular dependency: step1 -> step2 -> step3 -> step1
    step1 = ProofStep(step_id="s1", rule="ASSUME", premises=["s3"], conclusion="A")
    step2 = ProofStep(step_id="s2", rule="MODUS_PONENS", premises=["s1"], conclusion="B")
    step3 = ProofStep(step_id="s3", rule="AND_INTRO", premises=["s2"], conclusion="C")

    proof.steps = [step1, step2, step3]

    checker = ProofChecker()
    status = checker.check_proof(proof)

    assert status == ProofStatus.CONTRADICTORY, "Should detect cycle"


def test_proof_self_endorsement_detection():
    """Test that self-endorsing proofs are rejected."""
    proof = ProofObject(proposition="X is proven")

    # Step claims the main proposition without proper derivation
    step1 = ProofStep(
        step_id="self",
        rule="CLAIM",
        premises=[],  # No real premises
        conclusion="X is proven",
    )
    # Another step uses it as premise
    step2 = ProofStep(step_id="user", rule="USE", premises=["self"], conclusion="Therefore X")

    proof.steps = [step1, step2]

    checker = ProofChecker(allow_self_reference=False)
    status = checker.check_proof(proof)

    assert status == ProofStatus.CONTRADICTORY, "Should detect self-endorsement"


def test_proof_depth_limit():
    """Test that excessively deep proofs are rejected."""
    proof = ProofObject(proposition="Deep conclusion")

    # Create a chain of 25 steps (exceeds default limit of 20)
    for i in range(25):
        step = ProofStep(
            step_id=f"s{i}",
            rule="CHAIN",
            premises=[f"s{i-1}"] if i > 0 else [],
            conclusion=f"C{i}",
        )
        proof.steps.append(step)

    checker = ProofChecker(max_proof_depth=20)
    status = checker.check_proof(proof)

    assert status == ProofStatus.REFUTED, "Should reject proof exceeding depth limit"


def test_proof_valid_simple():
    """Test that valid simple proofs are accepted."""
    proof = ProofObject(proposition="A AND B")
    proof.assumptions.add("A")
    proof.assumptions.add("B")

    step = ProofStep(step_id="s1", rule="AND_INTRO", premises=["A", "B"], conclusion="A AND B")
    proof.steps.append(step)

    checker = ProofChecker()
    status = checker.check_proof(proof)

    assert status == ProofStatus.PROVEN, "Should accept valid simple proof"


def test_proof_missing_premise():
    """Test that proofs with missing premises are rejected."""
    proof = ProofObject(proposition="B")

    step = ProofStep(
        step_id="s1",
        rule="ASSUME",
        premises=["nonexistent"],  # This premise doesn't exist
        conclusion="B",
    )
    proof.steps.append(step)

    checker = ProofChecker()
    status = checker.check_proof(proof)

    assert status == ProofStatus.REFUTED, "Should reject proof with missing premise"


def test_proof_depth_computation():
    """Test that proof depth is computed correctly."""
    proof = ProofObject(proposition="D")
    proof.assumptions.add("A")

    # Create tree: A -> B, A -> C, B+C -> D (depth 3)
    step1 = ProofStep(step_id="s1", rule="R1", premises=["A"], conclusion="B")
    step2 = ProofStep(step_id="s2", rule="R2", premises=["A"], conclusion="C")
    step3 = ProofStep(step_id="s3", rule="R3", premises=["s1", "s2"], conclusion="D")

    proof.steps = [step1, step2, step3]

    checker = ProofChecker(max_proof_depth=5)
    status = checker.check_proof(proof)

    # Should pass with depth limit of 5
    assert status == ProofStatus.PROVEN

    # Should fail with depth limit of 1 (tree has depth 2: A->B/C, then D)
    checker_strict = ProofChecker(max_proof_depth=1)
    status_strict = checker_strict.check_proof(proof)
    assert status_strict == ProofStatus.REFUTED


def test_proof_with_constraint_verification():
    """Test proof checking with external constraint verifier."""
    proof = ProofObject(proposition="Safe composition")

    cref = ConstraintRef(id="c1", expression="NO_EXFIL")
    proof.required_invariants.add(cref)
    proof.claimed_satisfactions["c1"] = True

    step = ProofStep(step_id="s1", rule="CHECK", premises=[], conclusion="Safe")
    proof.steps.append(step)

    # With valid constraint verifier
    def valid_verifier(c):
        return True  # All constraints valid

    checker = ProofChecker(constraint_verifier=valid_verifier)
    status = checker.check_proof(proof)
    assert status == ProofStatus.PROVEN

    # With failing constraint verifier
    def failing_verifier(c):
        return False  # Constraint violated

    checker_fail = ProofChecker(constraint_verifier=failing_verifier)
    status_fail = checker_fail.check_proof(proof)
    assert status_fail == ProofStatus.REFUTED

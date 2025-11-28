"""
Test metadata signing and tampering detection.
"""


def test_metadata_tamper():
    """Test that tampering with kernel metadata is detected."""
    from src.kernels.metadata import KernelMetadata, sign_metadata, verify_metadata

    # use HMAC fallback for test
    secret = b"test-secret-rotatable"
    meta = KernelMetadata(
        kernel_id="k1",
        type="ETHICAL",
        warrant_threshold=0.9,
        veto_power=5,
        proof_burden="value_alignment",
    )
    signed = sign_metadata(meta, hmac_secret=secret)
    assert verify_metadata(signed, hmac_secret=secret)

    # mutate veto_power
    tampered = KernelMetadata(
        kernel_id=signed.kernel_id,
        type=signed.type,
        warrant_threshold=signed.warrant_threshold,
        veto_power=10,  # TAMPERED
        proof_burden=signed.proof_burden,
        signature=signed.signature,
    )
    assert not verify_metadata(tampered, hmac_secret=secret)


def test_metadata_signature_missing():
    """Test that unsigned metadata fails verification."""
    from src.kernels.metadata import KernelMetadata, verify_metadata

    secret = b"test-secret"
    meta = KernelMetadata(
        kernel_id="k2",
        type="LOGICAL",
        warrant_threshold=0.5,
        veto_power=1,
        proof_burden="formal",
    )
    # No signature
    assert not verify_metadata(meta, hmac_secret=secret)


def test_metadata_type_mutation():
    """Test that changing kernel type breaks signature."""
    from src.kernels.metadata import KernelMetadata, sign_metadata, verify_metadata

    secret = b"another-test-secret"
    meta = KernelMetadata(
        kernel_id="k3",
        type="TEACHER",
        warrant_threshold=0.8,
        veto_power=3,
        proof_burden="pedagogical",
    )
    signed = sign_metadata(meta, hmac_secret=secret)
    assert verify_metadata(signed, hmac_secret=secret)

    # Change type
    tampered = KernelMetadata(
        kernel_id=signed.kernel_id,
        type="STUDENT",  # TAMPERED
        warrant_threshold=signed.warrant_threshold,
        veto_power=signed.veto_power,
        proof_burden=signed.proof_burden,
        signature=signed.signature,
    )
    assert not verify_metadata(tampered, hmac_secret=secret)

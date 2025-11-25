"""Test kernel attestation system."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.governance.kernel_attestation import (  # noqa: E402
    KernelAttestationRegistry,
    verify_kernel_or_fail,
)


def test_kernel_attestation() -> None:
    """Test kernel attestation and verification."""
    from src.registry.kernel_registry import (  # noqa: E402
        AmplifierKernel,
        CompositionKernel,
        RiskActionKernel,
    )

    print("🔐 Testing kernel attestation system...\n")

    # Initialize registry
    registry = KernelAttestationRegistry()

    # Verify all production kernels are attested
    kernels = [
        ("RiskActionKernel", RiskActionKernel),
        ("AmplifierKernel", AmplifierKernel),
        ("CompositionKernel", CompositionKernel),
    ]

    for kernel_name, kernel_class in kernels:
        # Check approved
        assert registry.is_kernel_approved(
            kernel_name
        ), f"Kernel not approved: {kernel_name}. Run: python scripts/attest_kernels.py"

        # Verify hash
        assert registry.verify_kernel(
            kernel_name, kernel_class
        ), f"Kernel hash mismatch: {kernel_name}"

        print(f"✅ {kernel_name} verified")

    print("\n✅ All production kernels verified successfully!")
    print()

    # Test verify_kernel_or_fail helper
    print("Testing verify_kernel_or_fail helper...")
    try:
        verify_kernel_or_fail("RiskActionKernel", RiskActionKernel)
        print("✅ verify_kernel_or_fail passed for approved kernel")
    except RuntimeError as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    # Test rejection of unknown kernel
    print("\nTesting rejection of unknown kernel...")

    class EvilKernel:
        """Malicious kernel injected by attacker."""

        pass

    try:
        verify_kernel_or_fail("EvilKernel", EvilKernel)
        print("❌ EvilKernel incorrectly approved!")
        sys.exit(1)
    except RuntimeError as e:
        print(f"✅ EvilKernel correctly rejected: {e}")

    print("\n✅ Kernel attestation system working correctly!")


if __name__ == "__main__":
    test_kernel_attestation()

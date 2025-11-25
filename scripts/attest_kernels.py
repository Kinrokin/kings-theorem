"""Script to attest approved kernels and generate kernel allowlist.

Usage:
    python scripts/attest_kernels.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.governance.kernel_attestation import KernelAttestationRegistry  # noqa: E402


def main() -> None:
    """Attest all production kernels and save allowlist."""
    # Import kernels
    from src.registry.kernel_registry import (  # noqa: E402
        AmplifierKernel,
        CompositionKernel,
        RiskActionKernel,
    )

    registry = KernelAttestationRegistry()

    # Attest kernels
    print("🔐 Attesting production kernels...\n")

    kernels = [
        ("RiskActionKernel", RiskActionKernel),
        ("AmplifierKernel", AmplifierKernel),
        ("CompositionKernel", CompositionKernel),
    ]

    for kernel_name, kernel_class in kernels:
        attestation = registry.attest_kernel(kernel_name, kernel_class, approved_by="operator@local")
        print(f"✅ Attested: {kernel_name}")
        print(f"   Module: {attestation.module_path}")
        print(f"   Hash: {attestation.module_hash[:16]}...")
        print(f"   Approved by: {attestation.approved_by}")
        print()

    # Save allowlist
    registry.save_allowlist()
    print(f"✅ Allowlist saved: {registry.allowlist_path}")
    print()
    print("⚠️  Next steps:")
    print("   1. Review generated config/kernel_allowlist.yml")
    print("   2. Wire kernel verification into Arbiter (src/kernels/arbiter_v47.py)")
    print("   3. Enable KT_VERIFY_KERNELS=1 in production")


if __name__ == "__main__":
    main()

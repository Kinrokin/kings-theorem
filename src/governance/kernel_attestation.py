"""Kernel attestation registry for preventing unauthorized kernel injection.

Computes SHA256 hashes of approved kernels and maintains allowlist.
Prevents EvilKernel attacks by rejecting unknown/unattested kernels at runtime.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from src.crypto import compute_file_hash


@dataclass
class KernelAttestation:
    """Attestation record for approved kernel."""

    kernel_name: str
    module_path: str
    module_hash: str
    class_name: str
    approved_by: str
    timestamp: str


class KernelAttestationRegistry:
    """Registry of approved kernels with cryptographic attestation."""

    def __init__(self, allowlist_path: Optional[Path] = None) -> None:
        """Initialize registry from allowlist file.

        Args:
            allowlist_path: Path to kernel allowlist YAML (default: config/kernel_allowlist.yml)
        """
        if allowlist_path is None:
            allowlist_path = Path(__file__).resolve().parents[2] / "config" / "kernel_allowlist.yml"

        self.allowlist_path = allowlist_path
        self.attestations: Dict[str, KernelAttestation] = {}

        # Load allowlist if exists
        if allowlist_path.exists():
            self._load_allowlist()

    def _load_allowlist(self) -> None:
        """Load kernel allowlist from YAML file."""
        import yaml

        with open(self.allowlist_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for kernel_name, record in data.get("kernels", {}).items():
            attestation = KernelAttestation(
                kernel_name=kernel_name,
                module_path=record["module_path"],
                module_hash=record["module_hash"],
                class_name=record["class_name"],
                approved_by=record["approved_by"],
                timestamp=record["timestamp"],
            )
            self.attestations[kernel_name] = attestation

    def compute_kernel_hash(self, kernel_class: type) -> str:
        """Compute SHA256 hash of kernel module source code.

        Args:
            kernel_class: Kernel class to hash (e.g., RiskActionKernel)

        Returns:
            Hex-encoded SHA256 hash of module source
        """
        module = inspect.getmodule(kernel_class)
        if module is None or module.__file__ is None:
            raise ValueError(f"Cannot determine module for kernel: {kernel_class.__name__}")

        module_path = Path(module.__file__)
        return compute_file_hash(str(module_path))

    def attest_kernel(self, kernel_name: str, kernel_class: type, approved_by: str) -> KernelAttestation:
        """Attest a kernel by computing its hash and adding to registry.

        Args:
            kernel_name: Name to register (e.g., "RiskActionKernel")
            kernel_class: Kernel class to attest
            approved_by: Identifier of approver (e.g., "operator@local")

        Returns:
            KernelAttestation record
        """
        from datetime import datetime, timezone

        module = inspect.getmodule(kernel_class)
        if module is None or module.__file__ is None:
            raise ValueError(f"Cannot determine module for kernel: {kernel_class.__name__}")

        module_path = module.__file__
        module_hash = self.compute_kernel_hash(kernel_class)

        attestation = KernelAttestation(
            kernel_name=kernel_name,
            module_path=module_path,
            module_hash=module_hash,
            class_name=kernel_class.__name__,
            approved_by=approved_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self.attestations[kernel_name] = attestation
        return attestation

    def verify_kernel(self, kernel_name: str, kernel_class: type) -> bool:
        """Verify kernel matches attestation record.

        Args:
            kernel_name: Name of kernel to verify
            kernel_class: Kernel class instance to verify

        Returns:
            True if kernel hash matches attestation, False otherwise
        """
        if kernel_name not in self.attestations:
            return False

        attestation = self.attestations[kernel_name]
        current_hash = self.compute_kernel_hash(kernel_class)

        return current_hash == attestation.module_hash

    def is_kernel_approved(self, kernel_name: str) -> bool:
        """Check if kernel is in approved allowlist.

        Args:
            kernel_name: Name of kernel to check

        Returns:
            True if kernel is approved, False otherwise
        """
        return kernel_name in self.attestations

    def save_allowlist(self) -> None:
        """Save kernel attestations to allowlist YAML file."""
        import yaml

        data = {
            "version": 1,
            "kernels": {
                name: {
                    "module_path": att.module_path,
                    "module_hash": att.module_hash,
                    "class_name": att.class_name,
                    "approved_by": att.approved_by,
                    "timestamp": att.timestamp,
                }
                for name, att in self.attestations.items()
            },
        }

        self.allowlist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.allowlist_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)

    def get_all_attestations(self) -> List[KernelAttestation]:
        """Get all kernel attestations in registry.

        Returns:
            List of all kernel attestation records
        """
        return list(self.attestations.values())


# Global registry instance
_registry: Optional[KernelAttestationRegistry] = None


def get_registry() -> KernelAttestationRegistry:
    """Get global kernel attestation registry (singleton).

    Returns:
        KernelAttestationRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = KernelAttestationRegistry()
    return _registry


def verify_kernel_or_fail(kernel_name: str, kernel_class: type) -> None:
    """Verify kernel attestation or raise error.

    Args:
        kernel_name: Name of kernel to verify
        kernel_class: Kernel class to verify

    Raises:
        RuntimeError: If kernel not approved or hash mismatch
    """
    registry = get_registry()

    if not registry.is_kernel_approved(kernel_name):
        raise RuntimeError(
            f"Kernel not approved: {kernel_name}. " f"Run: python scripts/attest_kernels.py to generate allowlist."
        )

    if not registry.verify_kernel(kernel_name, kernel_class):
        raise RuntimeError(
            f"Kernel hash mismatch: {kernel_name}. "
            f"Kernel code has been modified since attestation. "
            f"Rejecting to prevent EvilKernel injection."
        )

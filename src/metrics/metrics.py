from __future__ import annotations
from prometheus_client import Counter

# Manifest verification
kt_manifest_verifications_total = Counter(
    "kt_manifest_verifications_total", "Total manifest verifications",
    labelnames=("result",)
)

# Proof checking
kt_proof_checks_total = Counter(
    "kt_proof_checks_total", "Total proof checks",
    labelnames=("result",)
)

# Kernel attestation
kt_kernel_attestation_total = Counter(
    "kt_kernel_attestation_total", "Total kernel attestation checks",
    labelnames=("result",)
)

def record_manifest_verification(success: bool) -> None:
    kt_manifest_verifications_total.labels(result="success" if success else "failure").inc()

def record_proof_check(success: bool) -> None:
    kt_proof_checks_total.labels(result="success" if success else "failure").inc()

def record_kernel_attestation(success: bool) -> None:
    kt_kernel_attestation_total.labels(result="success" if success else "failure").inc()

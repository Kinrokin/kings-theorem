from __future__ import annotations

try:
    from prometheus_client import Counter  # type: ignore
except ImportError:  # Graceful fallback when prometheus_client isn't installed

    class _NoOpLabels:
        def inc(self) -> None:
            return None

    class _NoOpCounter:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def labels(self, **kwargs) -> _NoOpLabels:  # type: ignore
            return _NoOpLabels()

    def Counter(*args, **kwargs):  # type: ignore
        return _NoOpCounter()


# Manifest verification
kt_manifest_verifications_total = Counter(
    "kt_manifest_verifications_total",
    "Total manifest verifications",
    labelnames=("result",),
)

# Proof checking
kt_proof_checks_total = Counter("kt_proof_checks_total", "Total proof checks", labelnames=("result",))

# Kernel attestation
kt_kernel_attestation_total = Counter(
    "kt_kernel_attestation_total",
    "Total kernel attestation checks",
    labelnames=("result",),
)


def record_manifest_verification(success: bool) -> None:
    kt_manifest_verifications_total.labels(result="success" if success else "failure").inc()


def record_proof_check(success: bool) -> None:
    kt_proof_checks_total.labels(result="success" if success else "failure").inc()


def record_kernel_attestation(success: bool) -> None:
    kt_kernel_attestation_total.labels(result="success" if success else "failure").inc()

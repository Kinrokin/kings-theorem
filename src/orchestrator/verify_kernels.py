# src/orchestrator/verify_kernels.py
from __future__ import annotations
import json
import logging
from typing import Dict, Any, List, Optional

from src.manifest.signature import verify_manifest
from src.metrics.metrics import record_kernel_attestation

logger = logging.getLogger("kt.orchestrator.verify_kernels")
logger.setLevel(logging.INFO)

def verify_kernel_metadata_list(
    kernel_manifests: List[Dict[str, Any]],
    pubkey_pem: Optional[bytes] = None,
    hmac_secret: Optional[bytes] = None,
    raise_on_arbiter_failure: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Verify a list of kernel manifests (each is a dict that must include
    'kernel_id', 'type', 'veto_power', 'warrant', and signature fields produced by sign_manifest).
    Returns a dict mapping kernel_id -> verification result dict:
      { kernel_id: {"ok": bool, "reason": str } }
    If raise_on_arbiter_failure=True, raises Exception if any Arbiter kernel fails verification.
    """
    results = {}
    arbiter_failures = []
    
    for m in kernel_manifests:
        kid = m.get("kernel_id", "<unknown>")
        ok, reason = verify_manifest(m, pubkey_pem=pubkey_pem, hmac_secret=hmac_secret)
        results[kid] = {"ok": ok, "reason": reason}
        if not ok:
            logger.warning("Kernel metadata verification failed for %s: %s", kid, reason)
            # Track Arbiter failures specifically
            if m.get("type") == "Arbiter":
                arbiter_failures.append(kid)
        try:
            record_kernel_attestation(bool(ok))
        except Exception:
            pass
    
    # Optionally fail-fast if any Arbiter fails verification
    if raise_on_arbiter_failure and arbiter_failures:
        raise RuntimeError(f"Critical kernel verification failed for arbiter(s): {arbiter_failures}")
    
    return results

def boot_verify_and_enforce(
    kernel_manifests: List[Dict[str, Any]],
    pubkey_pem: Optional[bytes] = None,
    hmac_secret: Optional[bytes] = None,
) -> None:
    """
    Boot-time enforcement: verifies kernels and raises on critical failures.
    Call this early in orchestrator startup.
    """
    # Use raise_on_arbiter_failure=True for production boot-time checks
    results = verify_kernel_metadata_list(
        kernel_manifests, 
        pubkey_pem=pubkey_pem, 
        hmac_secret=hmac_secret,
        raise_on_arbiter_failure=True
    )
    # enforce: at least one signed Arbiter must exist and be ok
    arbiter_ok = False
    for m in kernel_manifests:
        if m.get("type") == "Arbiter":
            if results.get(m.get("kernel_id"), {}).get("ok"):
                arbiter_ok = True
                break
    if not arbiter_ok:
        raise RuntimeError("No valid Arbiter kernel found; refusing to start orchestrator.")
    logger.info("Kernel metadata verification passed. Orchestrator may proceed.")

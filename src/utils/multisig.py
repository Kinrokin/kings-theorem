import os
from typing import Dict, List, Optional, Set

from .crypto import verify_signature

# Define the critical action statuses that REQUIRE 2-of-2 signature
CRITICAL_STATUSES = ["FREEZE", "HALT", "OVERRIDE"]


class InvalidSignatureError(Exception):
    """Raised when signature verification fails."""


class MultisigPolicyError(Exception):
    """Raised when the required number of signatures is not met."""


def check_multisig_required(proposal_status: str) -> bool:
    """Checks if a given proposal status requires the critical 2-of-2 multisig."""
    return proposal_status.upper() in CRITICAL_STATUSES


def verify_multisig(
    data_to_verify: str,
    signatures: List[Dict[str, str]],
    required_count: int,
    policy_status: str = "EXECUTE",
    keys_dir: Optional[str] = None,
) -> bool:
    """
    Verifies a set of signatures against a piece of data based on policy.

    Args:
        data_to_verify: The original proposal hash/token.
        signatures: List of dictionaries, each containing 'key_id' and 'signature'.
        required_count: The minimum number of unique, valid signatures needed.
        policy_status: The status of the proposal (e.g., EXECUTE, HALT).

    Returns:
        True if the signature count meets the required policy, False otherwise.

    Raises:
        MultisigPolicyError: If insufficient valid signatures are provided.
        InvalidSignatureError: If a signature fails cryptographic check.
    """
    if required_count == 0:
        return True

    valid_signature_keys: Set[str] = set()

    # 1. Check Policy Override (S1 Enforcement)
    if check_multisig_required(policy_status.upper()) and required_count < 2:
        raise MultisigPolicyError(
            f"Critical status '{policy_status}' requires a minimum of 2 valid signatures (2-of-2 policy)."
        )

    # 2. Iterate and Verify
    for sig_info in signatures:
        key_id = sig_info.get("key_id")
        signature = sig_info.get("signature")

        if not key_id or not signature:
            continue

        # Resolve public key path
        pub_path = key_id
        if keys_dir:
            # if key_id already looks like a file, use directly; else append
            candidate = os.path.join(keys_dir, key_id)
            if os.path.exists(candidate):
                pub_path = candidate
            else:
                # try common extensions
                for ext in (".pub", ".pem"):
                    candidate_ext = candidate + ext
                    if os.path.exists(candidate_ext):
                        pub_path = candidate_ext
                        break

        try:
            is_valid = verify_signature(
                pub_path, data_to_verify.encode() if isinstance(data_to_verify, str) else data_to_verify, signature
            )
        except Exception as e:
            raise InvalidSignatureError(f"Verification failed for key {key_id}: {e}")

        if is_valid:
            valid_signature_keys.add(key_id)

    # 3. Final Check
    if len(valid_signature_keys) < required_count:
        raise MultisigPolicyError(
            f"Required signatures not met. Needed {required_count}, found {len(valid_signature_keys)}."
        )

    return True

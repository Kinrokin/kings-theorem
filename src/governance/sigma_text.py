import hashlib
import logging
from dataclasses import dataclass
from typing import List

from src.governance.guardrail_v2 import normalize_text

logger = logging.getLogger(__name__)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class SigmaText:
    """Zero-knowledge representation of text content.

    Stores only aggregate statistics and cryptographic hashes of tokens;
    avoids retaining raw content to reduce exposure in governance paths.

    Attributes:
        text_sha256: Hash of normalized text
        length: Character length of normalized text
        token_hashes: First N token hashes (stable order)
        alnum_ratio: Ratio of alphanumeric characters to total
    """

    text_sha256: str
    length: int
    token_hashes: List[str]
    alnum_ratio: float


def to_sigma_text(text: str, max_tokens: int = 32) -> SigmaText:
    """Convert raw text to σ-text features with no raw content leakage.

    Args:
        text: Raw string to transform
        max_tokens: Max token hashes to retain for diagnostics

    Returns:
        SigmaText dataclass with hashed features.
    """
    norm = normalize_text(text)
    text_hash = _sha256_hex(norm.encode("utf-8"))

    # Crude tokenization on whitespace
    tokens = [t for t in norm.split() if t]
    token_hashes = [_sha256_hex(t.encode("utf-8")) for t in tokens[:max_tokens]]

    if len(norm) > 0:
        alnum = sum(1 for c in norm if c.isalnum())
        alnum_ratio = alnum / len(norm)
    else:
        alnum_ratio = 0.0

    sigma = SigmaText(
        text_sha256=text_hash,
        length=len(norm),
        token_hashes=token_hashes,
        alnum_ratio=alnum_ratio,
    )
    logger.debug("Sigma computed: len=%d, alnum_ratio=%.3f", sigma.length, sigma.alnum_ratio)
    return sigma

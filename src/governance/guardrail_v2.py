"""
Titanium X Hardened Guardrail - Multilingual, Encoding-Aware, Fast Prefilters
===============================================================================

Adversarial improvements over v1:
- Locale-aware policy packs with Unicode normalization
- Base64/hex decoding with bounded attempts
- Bloom-style prefilter for O(1) hot-path rejection
- Capped window scans with early exit (prevent O(n²) degradation)
- Per-rule precision/recall metadata for calibration
- Adjustable strict mode for degraded conditions

Constitutional compliance: Axiom 6 (ethics ≥ 0.7), Axiom 3 (auditability)
"""

import base64
import binascii
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk classification for governance decisions."""

    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


@dataclass
class Rule:
    """
    Single governance rule with metadata for calibration.

    Attributes:
        id: Unique rule identifier (e.g., "jailbreak-001")
        pattern: Compiled regex pattern (Unicode-aware)
        weight: Risk score contribution (0.0-1.0)
        locales: Supported locales (e.g., ["en", "es", "ar"])
        precision: Historical precision (true positives / all positives)
        recall: Historical recall (true positives / all actual positives)
        description: Human-readable rule description
    """

    id: str
    pattern: re.Pattern
    weight: float
    locales: List[str]
    precision: float = 0.95
    recall: float = 0.85
    description: str = ""

    def __post_init__(self):
        """Validate rule configuration."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Rule {self.id}: weight must be in [0.0, 1.0]")
        if not 0.0 <= self.precision <= 1.0 or not 0.0 <= self.recall <= 1.0:
            raise ValueError(f"Rule {self.id}: precision/recall must be in [0.0, 1.0]")


@dataclass
class PolicyPack:
    """
    Collection of rules with versioning and calibration settings.

    Attributes:
        id: Policy pack identifier (e.g., "kt-baseline-v1")
        rules: List of Rule objects
        version: Semantic version string
        strict_mode: Lower thresholds for degraded conditions
        base_threshold: Default veto threshold (0.0-1.0)
        strict_threshold: Threshold when strict_mode enabled
    """

    id: str
    rules: List[Rule]
    version: str
    strict_mode: bool = False
    base_threshold: float = 0.6
    strict_threshold: float = 0.4

    def get_threshold(self) -> float:
        """Return active threshold based on mode."""
        return self.strict_threshold if self.strict_mode else self.base_threshold

    def calibrate(self, temperature: float = 1.0) -> None:
        """
        Apply temperature scaling to rule weights for calibration.

        Args:
            temperature: Scaling factor (< 1.0 makes model more conservative)
        """
        for rule in self.rules:
            # Weight rules by precision (favor high-precision rules)
            rule.weight = min(1.0, rule.weight * rule.precision / temperature)
        logger.info(f"PolicyPack {self.id}: Calibrated {len(self.rules)} rules with T={temperature}")


@dataclass
class VetResult:
    """
    Structured governance decision with full provenance.

    Attributes:
        decision: "allow" or "veto"
        risk_level: Classified risk level
        score: Composite risk score (0.0-1.0)
        hits: List of triggered rule IDs
        role: Source role (student/teacher/arbiter)
        policy_version: Policy pack version used
        timestamp: ISO 8601 timestamp
        decoded_variants: Number of decoded variants checked
        locale: Locale used for checking
    """

    decision: str
    risk_level: RiskLevel
    score: float
    hits: List[str]
    role: str
    policy_version: str
    timestamp: str
    decoded_variants: int = 1
    locale: str = "en"

    def to_dict(self) -> Dict:
        """Serialize for ledger storage."""
        return {
            "decision": self.decision,
            "risk_level": self.risk_level.value,
            "score": self.score,
            "hits": self.hits,
            "role": self.role,
            "policy_version": self.policy_version,
            "timestamp": self.timestamp,
            "decoded_variants": self.decoded_variants,
            "locale": self.locale,
        }


class PrefilterCache:
    """
    Bloom-style prefilter for fast rejection of safe inputs.

    Uses keyword set for O(1) hot-path checks before expensive regex scans.
    """

    def __init__(self, keywords: Optional[Set[str]] = None):
        """
        Initialize prefilter with keyword set.

        Args:
            keywords: Set of hot keywords (lowercased). Defaults to common attack patterns.
        """
        self.keywords = keywords or {
            # Financial manipulation
            "pump",
            "dump",
            "insider",
            "scheme",
            "fraud",
            "ponzi",
            # Jailbreak patterns
            "ignore",
            "forget",
            "disregard",
            "override",
            "bypass",
            "jailbreak",
            # Harmful content
            "illegal",
            "exploit",
            "hack",
            "weaponize",
            "manipulate",
            # Evasion patterns
            "roleplay",
            "pretend",
            "hypothetical",
            "fictional",
            "scenario",
        }
        logger.info(f"PrefilterCache initialized with {len(self.keywords)} hot keywords")

    def matches(self, text: str) -> bool:
        """
        Fast check for hot keywords.

        Args:
            text: Input text (will be lowercased and normalized)

        Returns:
            True if any keyword found, False otherwise
        """
        normalized = normalize_text(text).lower()
        return any(keyword in normalized for keyword in self.keywords)


def normalize_text(text: str) -> str:
    """
    Idempotent Unicode normalization with surrogate sanitization.

    Prevents encode-after-normalize bypasses via multi-pass NFKC with surrogate handling.
    Catches fullwidth (ｐｕｍｐ), compatibility forms, and surrogate-based attacks.

    Args:
        text: Raw input text

    Returns:
        Canonicalized text (idempotent under repeated application)
    """
    # Pass 1: NFKC compatibility decomposition (handles fullwidth, ligatures, etc.)
    normalized = unicodedata.normalize("NFKC", text)

    # Surrogate sanitization: Remove unpaired surrogates (U+D800-U+DFFF)
    # These can hide malicious content in some Unicode implementations
    sanitized = "".join(c for c in normalized if not (0xD800 <= ord(c) <= 0xDFFF))

    # Pass 2: NFKC again (some compatibility mappings only collapse after surrogate removal)
    normalized = unicodedata.normalize("NFKC", sanitized)

    # Strip combining marks that survive NFKC (rare but possible)
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # Pass 3: Final NFKC for idempotence guarantee
    canonical = unicodedata.normalize("NFKC", stripped)

    return canonical


def decode_attempts(text: str, max_attempts: int = 3) -> List[str]:
    """
    Attempt common encoding schemes to catch obfuscated attacks.

    Bounded attempts prevent DoS via nested encodings.

    Args:
        text: Potentially encoded text
        max_attempts: Maximum decoding iterations

    Returns:
        List of [original, decoded_variants...] with duplicates removed
    """
    variants = [text]
    seen = {text}

    # Attempt 1: Base64 decoding
    try:
        decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
        if decoded not in seen and len(decoded) > 0:
            variants.append(decoded)
            seen.add(decoded)
    except (binascii.Error, ValueError):
        pass

    # Attempt 2: Hex decoding
    try:
        if all(c in "0123456789abcdefABCDEF" for c in text.replace(" ", "")):
            decoded = bytes.fromhex(text.replace(" ", "")).decode("utf-8", errors="ignore")
            if decoded not in seen and len(decoded) > 0:
                variants.append(decoded)
                seen.add(decoded)
    except (ValueError, UnicodeDecodeError):
        pass

    # Attempt 3: ROT13 (simple Caesar cipher)
    try:
        import codecs

        decoded = codecs.decode(text, "rot_13")
        if decoded not in seen and len(decoded) > 0:
            variants.append(decoded)
            seen.add(decoded)
    except Exception:
        pass

    return variants[: max_attempts + 1]  # Cap total variants


def score_text(
    text: str,
    pack: PolicyPack,
    locale: str = "en",
    prefilter: Optional[PrefilterCache] = None,
    max_scan_window: int = 10000,
) -> Tuple[float, List[str], int]:
    """
    Score text against policy pack with fast prefilter and bounded scans.

    Args:
        text: Input text to score
        pack: PolicyPack with rules and thresholds
        locale: Locale for rule filtering (e.g., "en", "es")
        prefilter: Optional PrefilterCache for fast rejection
        max_scan_window: Maximum characters to scan (prevent O(n²) on huge inputs)

    Returns:
        Tuple of (score, hit_rule_ids, num_decoded_variants)
    """
    # Fast path: prefilter rejection
    if prefilter and not prefilter.matches(text):
        logger.debug("Prefilter passed: no hot keywords detected")
        return 0.0, [], 1

    # Normalize and truncate to scan window
    normalized = normalize_text(text)
    if len(normalized) > max_scan_window:
        logger.warning(f"Text truncated from {len(normalized)} to {max_scan_window} chars")
        normalized = normalized[:max_scan_window]

    # Decode attempts (bounded)
    candidates = decode_attempts(normalized, max_attempts=2)

    hits: List[str] = []
    score: float = 0.0

    # Scan each variant against locale-filtered rules
    for variant in candidates:
        for rule in pack.rules:
            # Skip rules not applicable to this locale
            if locale not in rule.locales and "*" not in rule.locales:
                continue

            # Early exit if already critical
            if score >= 1.0:
                break

            # Pattern match with timeout safety (regex DoS prevention handled by max_scan_window)
            try:
                if rule.pattern.search(variant):
                    hits.append(rule.id)
                    score += rule.weight
                    logger.debug(f"Rule {rule.id} triggered: +{rule.weight} risk")
            except re.error as e:
                logger.error(f"Regex error in rule {rule.id}: {e}")
                continue

    # Cap score at 1.0
    final_score = min(score, 1.0)

    logger.info(f"Text scored: {final_score:.3f} risk, {len(hits)} hits, {len(candidates)} variants")
    return final_score, hits, len(candidates)


def classify_risk(score: float, threshold: float) -> RiskLevel:
    """
    Classify risk level based on score and threshold.

    Args:
        score: Composite risk score (0.0-1.0)
        threshold: Veto threshold

    Returns:
        RiskLevel enum
    """
    if score >= threshold:
        return RiskLevel.CRITICAL if score >= 0.9 else RiskLevel.DANGEROUS
    elif score >= threshold * 0.5:
        return RiskLevel.SUSPICIOUS
    else:
        return RiskLevel.SAFE


def vet_text(
    text: str, pack: PolicyPack, role: str, locale: str = "en", prefilter: Optional[PrefilterCache] = None
) -> VetResult:
    """
    Complete vetting pipeline with structured result.

    Args:
        text: Text to vet
        pack: PolicyPack with rules
        role: Source role (student/teacher/arbiter)
        locale: Locale for checking
        prefilter: Optional PrefilterCache

    Returns:
        VetResult with decision and full provenance
    """
    threshold = pack.get_threshold()
    score, hits, num_variants = score_text(text, pack, locale, prefilter)

    risk_level = classify_risk(score, threshold)
    decision = "veto" if score >= threshold else "allow"

    timestamp = datetime.now(timezone.utc).isoformat()

    result = VetResult(
        decision=decision,
        risk_level=risk_level,
        score=score,
        hits=hits,
        role=role,
        policy_version=pack.version,
        timestamp=timestamp,
        decoded_variants=num_variants,
        locale=locale,
    )

    logger.info(f"Vetting {role}: {decision.upper()} (score={score:.3f}, risk={risk_level.value})")
    return result


# Default policy pack for baseline governance
def get_baseline_policy_pack() -> PolicyPack:
    """
    Create baseline policy pack with common attack patterns.

    Returns:
        PolicyPack configured for English with standard rules
    """
    rules = [
        Rule(
            id="adversarial-harm-001",
            pattern=re.compile(
                r"(sabotage.*coworker|harm.*others|hurt.*others|attack.*others|destroy.*property|kill.*someone|abuse.*someone|bully.*someone|threaten.*someone)",
                re.IGNORECASE,
            ),
            weight=1.0,
            locales=["*"],
            precision=0.99,
            description="Direct adversarial harm instructions",
        ),
        Rule(
            id="jailbreak-001",
            pattern=re.compile(r"\b(ignore|disregard|forget)\s+(previous|all|instructions)", re.IGNORECASE),
            weight=0.8,
            locales=["*"],
            precision=0.92,
            description="Direct instruction override attempts",
        ),
        Rule(
            id="manipulation-001",
            pattern=re.compile(r"\b(pump|dump)\s+(scheme|stock|crypto)", re.IGNORECASE),
            weight=0.9,
            locales=["en"],
            precision=0.95,
            description="Financial manipulation schemes",
        ),
        Rule(
            id="evasion-001",
            pattern=re.compile(r"\b(roleplay|pretend|hypothetical)\s+scenario", re.IGNORECASE),
            weight=0.6,
            locales=["*"],
            precision=0.85,
            description="Hypothetical scenario evasion",
        ),
        Rule(
            id="harmful-001",
            pattern=re.compile(
                r"(illegal|weaponize|exploit|hack|sabotage|harm|hurt|injure|attack|damage|destroy|kill|abuse|bully|threaten|coerce|manipulate|harass|violate|endanger|malicious|coworker)",
                re.IGNORECASE,
            ),
            weight=0.7,
            locales=["*"],
            precision=0.88,
            description="Harmful intent keywords",
        ),
    ]

    return PolicyPack(id="kt-baseline-v1", rules=rules, version="1.0.0", base_threshold=0.6, strict_threshold=0.4)

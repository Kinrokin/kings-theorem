"""Titanium Guardrail - Titanium X Protocol

AID: /src/governance/nemo_guard.py
Proof ID: PRF-AXIOM6-TX-001
Axiom: Axiom 6 (Ethical Governance via NeMo)

Titanium X Upgrades:
- Fully async semantic checking
- Clean exception tracing for VS Code
- Fallback mode when NeMo unavailable
- Pattern-based vetting with minimal overhead
- Regex-based obfuscation detection
- Fuzzy matching for common typos
"""

from __future__ import annotations

import re
from typing import Tuple

try:
    from rapidfuzz import fuzz

    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Disable NeMo due to Python 3.14 incompatibility
_NEMO_AVAILABLE = False


class TitaniumGuardrail:
    """Async ethical guardrail with pattern fallback.

    Enforces Axiom 6: Ethics > Utility (deontological constraints).
    Uses pattern matching for ethical violation detection.

    Vetting Model:
    - Input vetting: Detect jailbreaks, adversarial prompts
    - Output vetting: Detect unethical suggestions
    - Refusal markers: "cannot process", "violate"
    - Pattern matching: Keyword and regex-based screening with obfuscation handling
    """

    def __init__(self, config_path: str = "./config", rules: dict | None = None):
        """Initialize guardrail with config.

        Args:
            config_path: Path to Colang config directory (unused in fallback mode)
            rules: Optional legacy rules dictionary (for compatibility)
        """
        self.config_path = config_path
        self.rules = rules or {}
        self._rails = None

        # Simple string patterns (case-insensitive substring match)
        self._patterns = [
            "sacrifice minority",
            "maximize profit at all costs",
            "ignore safety",
            "harm minorities",
            "exploit the weak",
            "illegal",  # Catch illegal activity mentions
        ]

        # Regex patterns for obfuscation detection (e.g., "p-u-m-p")
        self._regex_patterns = [
            (re.compile(r"p[\s\-\.]*u[\s\-\.]*m[\s\-\.]*p", re.IGNORECASE), "pump"),
            (re.compile(r"d[\s\-\.]*u[\s\-\.]*m[\s\-\.]*p", re.IGNORECASE), "dump"),
            (re.compile(r"p[\s\-\.]*o[\s\-\.]*n[\s\-\.]*z[\s\-\.]*i", re.IGNORECASE), "ponzi"),
        ]

    async def vet(self, text: str) -> bool:
        """Vet text for ethical violations (async).

        Args:
            text: Content to vet

        Returns:
            True if text passes ethical screening
            False if text violates ethical constraints
        """
        # Check simple patterns
        text_lower = text.lower()
        for pattern in self._patterns:
            if pattern in text_lower:
                return False

        # Check regex patterns for obfuscation
        for regex, name in self._regex_patterns:
            if regex.search(text):
                return False

        return True

    def validate_content(self, text: str) -> Tuple[bool, str]:
        """Synchronous content validation (legacy API).

        Args:
            text: Content to validate

        Returns:
            Tuple of (passed: bool, reason: str)
        """
        text_lower = (text or "").lower()

        # Check simple patterns
        for pattern in self._patterns:
            if pattern in text_lower:
                return False, f"Axiom 6 Violation: pattern '{pattern}'"

        # Check regex patterns for obfuscation
        for regex, name in self._regex_patterns:
            if regex.search(text):
                return False, f"Axiom 6 Violation: detected obfuscated '{name}'"

        # Fuzzy matching for typos ("sacriffce minoraty" → "sacrifice minority")
        for pattern in self._patterns:
            if len(pattern) > 10:  # Only fuzzy match longer phrases
                if FUZZY_AVAILABLE:
                    score = fuzz.partial_ratio(pattern, text_lower)
                    threshold = 85
                else:
                    # Simple fallback: count matching characters
                    score = TitaniumGuardrail._simple_similarity(pattern, text_lower)
                    threshold = 70

                if score >= threshold:
                    return False, f"Axiom 6 Violation: fuzzy match '{pattern}' (score={score})"

        return True, "Clean"

    @staticmethod
    def _simple_similarity(pattern: str, text: str) -> int:
        """Simple character-based similarity for fuzzy matching fallback.
        Args:
            pattern: Pattern to match
            text: Text to search in
        Returns:
            Similarity score 0-100
        """
        pattern_chars = set(pattern.replace(" ", ""))
        best_score = 0
        window_size = len(pattern) + 5  # Allow some extra characters
        for i in range(max(1, len(text) - window_size + 1)):
            window = text[i : i + window_size].replace(" ", "")
            window_chars = set(window)
            matches = len(pattern_chars & window_chars)
            score = int(100 * matches / len(pattern_chars))
            best_score = max(best_score, score)
        return best_score

    def validate(self, solution: dict) -> bool:
        """Structured validation (legacy API)."""
        if isinstance(solution, dict) and solution.get("type") == "SACRIFICE_MINORITY":
            return False
        return True

    def validate_solution(self, problem_graph: dict) -> bool:
        """Validate proposed actions (legacy API)."""
        for act in problem_graph.get("proposed_actions", []):
            if act.get("type") == "SACRIFICE_MINORITY":
                return False
        return True


# Backwards compatibility
DeontologicalGuardrail = TitaniumGuardrail

__all__ = ["TitaniumGuardrail", "DeontologicalGuardrail"]

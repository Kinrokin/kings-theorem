"""
AID: /src/governance/guardrail_dg_v1.py
Proof ID: PRF-DG-002-REGEX
Axiom: Axiom 6: Ethical Governance (Advanced)
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Tuple

logger = logging.getLogger(__name__)


class DeontologicalGuardrail:
    def __init__(self, rules: dict):
        self.rules = rules
        # Regex patterns to catch evasion (e.g. "p.u.m.p", "illegal")
        self.forbidden_patterns = [
            r"ignore\s+safety",
            r"sacrifice\s+minority",
            r"pump\s*[-_.]?\s*and\s*[-_.]?\s*dump",  # Catches "pump-and-dump", "pump and dump"
            r"p\W*u\W*m\W*p",
            r"d\W*u\W*m\W*p",
            r"harm\s+user",
            r"illegal\s+activity",
            r"market\s+manipulation",
        ]
        # Also keep plain keyword forms for fuzzy matching fallback
        self.forbidden_keywords = [
            "ignore safety",
            "sacrifice minority",
            "pump and dump",
            "harm user",
            "illegal activity",
            "market manipulation",
        ]

    def validate_content(self, text: str) -> Tuple[bool, str]:
        """
        Scans generated text for Axiom violations using Regex.
        Returns: (Passed: bool, Reason: str)
        """
        if not text:
            return (False, "Empty Output")

        text_lower = text.lower()

        for pattern in self.forbidden_patterns:
            m = re.search(pattern, text_lower)
            if m:
                matched = m.group(0)
                # Derive a readable concept from the pattern by removing regex tokens
                concept = re.sub(r"\\[A-Za-z]", "", pattern)  # remove escaped tokens like \W, \s
                concept = re.sub(r"[\[\]\-\_\.\?\s\*]", "", concept)
                concept = re.sub(r"[^a-zA-Z]", "", concept).lower()
                reason = f"Axiom 6 Violation: Detected pattern '{pattern}' matched '{matched}' (concept='{concept}')"
                logger.warning("[GUARDRAIL] VETO: %s", reason)
                return (False, reason)

        # Fuzzy fallback for obfuscated or misspelled keywords
        if self._fuzzy_match(text_lower):
            # find which keyword matched best and report it
            best_kw = None
            best_score = 0.0
            matched_sub = ""
            for kw in self.forbidden_keywords:
                k = kw.lower()
                clen = len(k)
                for i in range(0, max(1, len(text_lower) - clen + 1)):
                    window = text_lower[i : i + clen + 20]
                    score = SequenceMatcher(None, k, window).ratio()
                    if score > best_score:
                        best_score = score
                        best_kw = k
                        matched_sub = window
            reason = f"Axiom 6 Violation: Fuzzy-detected concept '{best_kw}' matched '{matched_sub}' (score={best_score:.2f})"
            logger.warning("[GUARDRAIL] VETO: %s", reason)
            return (False, reason)

        return (True, "Clean")

    def validate(self, solution: dict) -> bool:
        # Legacy tag check
        if isinstance(solution, dict) and "type" in solution:
            if solution["type"] == "SACRIFICE_MINORITY" and self.rules.get("RULE_PROTECT_MINORITY"):
                return False
        return True

    def validate_solution(self, solution: dict) -> bool:
        """Structured solution validation.

        Rejects forbidden action flags regardless of accompanying rationale.
        Looks for top-level keys: proposed_actions, tags, actions.
        """
        if not isinstance(solution, dict):
            return False
        forbidden_action_types = {"SACRIFICE_MINORITY", "DANGEROUS_TRADE"}

        # Direct tags
        tags = solution.get("tags", [])
        if any(t.upper() in forbidden_action_types for t in tags if isinstance(t, str)):
            return False

        # Proposed actions list
        actions = solution.get("proposed_actions") or solution.get("actions") or []
        if isinstance(actions, list):
            for a in actions:
                if isinstance(a, dict):
                    atype = str(a.get("type", "")).upper()
                    if atype in forbidden_action_types:
                        return False
                elif isinstance(a, str) and a.upper() in forbidden_action_types:
                    return False

        # Numeric configs (example heuristic: disallow utility > 900 with minority sacrifice intent)
        for a in actions:
            if isinstance(a, dict):
                if str(a.get("type", "")).upper() == "SACRIFICE_MINORITY" and float(a.get("utility", 0)) > 900:
                    return False
        return True

    def _fuzzy_match(self, text: str, threshold: float = 0.85) -> bool:
        """Return True if any forbidden keyword is fuzzily close to text substrings."""
        text_lower = text.lower()
        for kw in self.forbidden_keywords:
            k = kw.lower()
            clen = len(k)
            if clen == 0:
                continue
            # sliding window sizes near the keyword length
            min_len = max(3, int(clen * 0.6))
            max_len = int(clen * 1.4) + 1
            for L in range(min_len, max_len + 1):
                for i in range(0, max(1, len(text_lower) - L + 1)):
                    window = text_lower[i : i + L]
                    score = SequenceMatcher(None, k, window).ratio()
                    if score >= threshold:
                        return True
        return False

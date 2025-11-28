"""
AID: /src/governance/guardrail_dg_v1.py
Proof ID: PRF-DG-002-REGEX
Axiom: Axiom 6: Ethical Governance (Advanced)

Level 4 Enhancement: Dual-Layer Guardrail (Symbolic + Semantic)
- Symbolic Layer: Regex patterns + fuzzy matching (deterministic, rule-based)
- Semantic Layer: Embedding-based intent detection (probabilistic, meaning-aware)
- Both layers logged to cryptographic ledger for full audit trail
"""

import logging
import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Lazy import semantic guard (optional dependency)
_semantic_guard = None
ENABLE_SEMANTIC_LAYER = os.getenv("ENABLE_SEMANTIC_EMBEDDINGS", "false").lower() in ("true", "1", "yes")


def _get_semantic_guard():
    """Lazy-load semantic guard to avoid circular imports and allow feature flag control."""
    global _semantic_guard
    if _semantic_guard is None and ENABLE_SEMANTIC_LAYER:
        try:
            from governance.semantic_guard import get_semantic_guard

            _semantic_guard = get_semantic_guard()
            logger.info("Semantic guard layer activated (dual-layer mode)")
        except Exception as e:
            logger.warning("Semantic guard unavailable: %s. Using symbolic-only mode.", e)
            _semantic_guard = False  # Mark as attempted but failed
    return _semantic_guard if _semantic_guard is not False else None


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
        Scans generated text for Axiom violations using Dual-Layer Guardrail.

        Layer 1 (Symbolic): Regex patterns + fuzzy keyword matching (deterministic)
        Layer 2 (Semantic): Embedding-based intent detection (probabilistic)

        Returns: (Passed: bool, Reason: str)
        """
        if not text:
            return (False, "Empty Output")

        text_lower = text.lower()

        # Layer 2: Semantic Neural Guard (if enabled)
        semantic_guard = _get_semantic_guard()
        neural_hits: List[Dict[str, Any]] = []
        if semantic_guard:
            try:
                result = semantic_guard.assess(text)
                if result.is_blocked:
                    reason = f"Axiom 6 Violation (Semantic Layer): {result.reason}"
                    logger.warning("[GUARDRAIL] SEMANTIC VETO: %s", reason)
                    neural_hits.append(
                        {
                            "layer": "semantic",
                            "blocked": True,
                            "reason": result.reason,
                            "semantic_score": result.semantic_score,
                            "fuzzy_score": result.fuzzy_score,
                            "anchor_match": result.anchor_match,
                            "mode_degraded": result.mode_degraded,
                        }
                    )
                    return (False, reason)
                else:
                    # Record telemetry even if passed (for auditing)
                    neural_hits.append(
                        {
                            "layer": "semantic",
                            "blocked": False,
                            "semantic_score": result.semantic_score,
                            "fuzzy_score": result.fuzzy_score,
                            "mode_degraded": result.mode_degraded,
                        }
                    )
            except Exception as e:
                logger.warning("[GUARDRAIL] Semantic layer error: %s. Falling back to symbolic only.", e)

        # Layer 1: Symbolic Regex Patterns
        for pattern in self.forbidden_patterns:
            m = re.search(pattern, text_lower)
            if m:
                matched = m.group(0)
                # Derive a readable concept from the pattern by removing regex tokens
                concept = re.sub(r"\\[A-Za-z]", "", pattern)  # remove escaped tokens like \W, \s
                concept = re.sub(r"[\[\]\-\_\.\?\s\*]", "", concept)
                concept = re.sub(r"[^a-zA-Z]", "", concept).lower()
                reason = f"Axiom 6 Violation (Symbolic Layer): Detected pattern '{pattern}' matched '{matched}' (concept='{concept}')"
                logger.warning("[GUARDRAIL] REGEX VETO: %s", reason)
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
            reason = f"Axiom 6 Violation (Fuzzy Layer): Fuzzy-detected concept '{best_kw}' matched '{matched_sub}' (score={best_score:.2f})"
            logger.warning("[GUARDRAIL] FUZZY VETO: %s", reason)
            return (False, reason)

        # All layers passed
        if neural_hits:
            logger.debug("[GUARDRAIL] Passed dual-layer validation. Neural telemetry: %s", neural_hits)
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

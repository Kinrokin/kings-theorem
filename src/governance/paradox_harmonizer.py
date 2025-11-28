"""Paradox Harmonizer — Meta-logic for constitutional verdicts (Level 5).

Aggregates multiple spec results (MTL-style) into a single decision using
weights and hard/soft constraints. Any hard violation triggers a VETO.
"""

from __future__ import annotations

from typing import Any, Dict, List


class ParadoxHarmonizer:
    """Compute a constitutional verdict from multiple spec results.

    Constitution schema example:
        {
            "specs": {
                "risk_bounded": {"weight": 2.0, "hard": True},
                "privacy": {"weight": 1.0, "hard": False},
            }
        }
    """

    def __init__(self, constitution: Dict[str, Any]):
        self.constitution = constitution

    def harmonize(self, mtl_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score results and return a unified decision.

        Args:
            mtl_results: List of spec evaluation dicts, e.g.
                [{"spec": "risk_bounded", "result": "SATISFIED"}, ...]

        Returns:
            Dict with decision ("VETO" | "ALLOW"), total_score, and details.
        """
        scored: List[Dict[str, Any]] = []
        hard_violations: List[Dict[str, Any]] = []

        specs_meta: Dict[str, Any] = self.constitution.get("specs", {})

        for r in mtl_results:
            spec_id = r.get("spec", "unknown")
            spec_meta = specs_meta.get(spec_id, {})
            weight = float(spec_meta.get("weight", 1.0))
            is_hard = bool(spec_meta.get("hard", False))
            result = r.get("result")

            score = 0.0
            if result == "SATISFIED":
                score += weight
            elif result == "VIOLATED":
                score -= weight * (2.0 if is_hard else 1.0)

            enriched = {**r, "score": score, "weight": weight, "hard": is_hard}
            scored.append(enriched)

            if is_hard and result == "VIOLATED":
                hard_violations.append(r)

        total_score = float(sum(x["score"] for x in scored))

        if hard_violations:
            return {
                "decision": "VETO",
                "reason": "HARD_SPEC_VIOLATION",
                "total_score": total_score,
                "violations": hard_violations,
                "all": scored,
            }

        return {
            "decision": "ALLOW",
            "reason": "ALL_HARD_SPECS_SATISFIED",
            "total_score": total_score,
            "all": scored,
        }

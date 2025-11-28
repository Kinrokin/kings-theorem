from typing import Dict

from ..utils.gov_config import gov_config


class TriGovernor:
    @staticmethod
    def _risk_tier(score: float) -> str:
        if score >= 0.8:
            return "CATASTROPHIC"
        if score >= 0.4:
            return "SEVERE"
        if score >= 0.2:
            return "MODERATE"
        return "LOW"

    def adjudicate(self, proposal: Dict) -> Dict:
        tags = proposal.get("tags", [])

        flags = {"integrity": "PASS", "temporal": "PASS", "causal": "PASS"}

        if "unethical" in tags or proposal.get("integrity_violation", False):
            flags["integrity"] = "VETO"

        replay_conf = float(proposal.get("replay_confidence", 1.0))
        if replay_conf < 0.6:
            flags["temporal"] = "FREEZE"

        warrant = float(proposal.get("warrant", 1.0))
        required_threshold = gov_config.get_warrant_threshold()
        warrant_tier = "LOW" if warrant < required_threshold else ("MID" if warrant < 0.8 else "HIGH")
        if warrant_tier == "LOW":
            flags["causal"] = "REJECT"

        aggregate_risk = float(proposal.get("aggregate_risk", 0.0))
        constraint_tension = float(proposal.get("constraint_tension", 0.0))
        risk_tier = proposal.get("risk_tier") or self._risk_tier(aggregate_risk)

        if flags["integrity"] == "VETO" and flags["temporal"] == "FREEZE":
            return {
                "decision": "TIER_5_HALT",
                "reason": "CONSTITUTIONAL SINGULARITY",
                "risk_score": 1.0,
                "audit_flags": {**flags, "risk_tier": risk_tier},
            }

        if risk_tier == "CATASTROPHIC":
            return {
                "decision": "TIER_5_HALT",
                "reason": "Catastrophic risk tier",
                "risk_score": min(max(aggregate_risk, 0.95), 1.0),
                "audit_flags": {**flags, "risk_tier": risk_tier},
            }

        if flags["integrity"] == "VETO" or constraint_tension > 0.7:
            return {
                "decision": "HALT",
                "reason": "Integrity veto or constraint tension",
                "risk_score": min(max(aggregate_risk, 0.95), 1.0),
                "audit_flags": {**flags, "risk_tier": risk_tier},
            }

        if flags["temporal"] == "FREEZE" or risk_tier == "SEVERE":
            return {
                "decision": "FREEZE",
                "reason": "Temporal freeze or severe risk tier",
                "risk_score": min(max(aggregate_risk, 0.8), 1.0),
                "audit_flags": {**flags, "risk_tier": risk_tier},
            }

        if flags["causal"] == "REJECT" or (risk_tier == "MODERATE" and warrant_tier == "LOW"):
            return {
                "decision": "DROP",
                "reason": "Causal rejection or moderate risk with low warrant",
                "risk_score": min(max(aggregate_risk, 0.5), 1.0),
                "audit_flags": {**flags, "risk_tier": risk_tier},
            }

        risk_score = aggregate_risk if warrant_tier == "MID" else min(aggregate_risk, 0.2)
        return {
            "decision": "EXECUTE",
            "risk_score": risk_score,
            "audit_flags": {**flags, "risk_tier": risk_tier},
        }

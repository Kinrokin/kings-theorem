from typing import Dict

from ..utils.gov_config import gov_config


class TriGovernor:
    def adjudicate(self, proposal: Dict) -> Dict:
        tags = proposal.get("tags", [])

        flags = {"integrity": "PASS", "temporal": "PASS", "causal": "PASS"}

        if "unethical" in tags or proposal.get("integrity_violation", False):
            flags["integrity"] = "VETO"

        replay_conf = float(proposal.get("replay_confidence", 1.0))
        # Keep existing temporal rule; could be driven by policy in future
        if replay_conf < 0.6:
            flags["temporal"] = "FREEZE"

        # Use governance-driven warrant threshold instead of hardcoded 0.6
        warrant = float(proposal.get("warrant", 1.0))
        required_threshold = gov_config.get_warrant_threshold()
        warrant_tier = "LOW" if warrant < required_threshold else ("MID" if warrant < 0.8 else "HIGH")
        if warrant_tier == "LOW":
            flags["causal"] = "REJECT"

        # CONSTITUTIONAL SINGULARITY: Integrity=VETO AND Temporal=FREEZE
        if flags["integrity"] == "VETO" and flags["temporal"] == "FREEZE":
            return {
                "decision": "TIER_5_HALT",
                "reason": "CONSTITUTIONAL SINGULARITY",
                "risk_score": 1.0,
                "audit_flags": flags,
            }

        if flags["integrity"] == "VETO":
            return {"decision": "HALT", "risk_score": 0.95, "audit_flags": flags}

        if flags["causal"] == "REJECT":
            return {"decision": "DROP", "risk_score": 0.5, "audit_flags": flags}

        if flags["temporal"] == "FREEZE":
            return {"decision": "FREEZE", "risk_score": 0.8, "audit_flags": flags}

        risk = 0.2 if warrant_tier == "MID" else 0.1
        return {"decision": "EXECUTE", "risk_score": risk, "audit_flags": flags}

from typing import Dict

class TriGovernor:
    def adjudicate(self, proposal: Dict) -> Dict:
        tags = proposal.get('tags',[])
        
        flags = {'integrity': 'PASS', 'temporal': 'PASS', 'causal': 'PASS'}

        if 'unethical' in tags or proposal.get('integrity_violation', False):
            flags['integrity'] = 'VETO'

        replay_conf = float(proposal.get('replay_confidence', 1.0))
        if replay_conf < 0.6:
            flags['temporal'] = 'FREEZE'
        
        warrant = float(proposal.get('warrant', 1.0))
        warrant_tier = 'LOW' if warrant < 0.6 else ('MID' if warrant < 0.8 else 'HIGH')
        if warrant_tier == 'LOW': flags['causal'] = 'REJECT'

        # CONSTITUTIONAL SINGULARITY: Integrity=VETO AND Temporal=FREEZE
        if flags['integrity'] == 'VETO' and flags['temporal'] == 'FREEZE':
            return {
                'decision': 'TIER_5_HALT',
                'reason': 'CONSTITUTIONAL SINGULARITY',
                'risk_score': 1.0,
                'audit_flags': flags
            }

        if flags['integrity'] == 'VETO':
            return {'decision': 'HALT', 'risk_score': 0.95, 'audit_flags': flags}

        if flags['causal'] == 'REJECT':
            return {'decision': 'DROP', 'risk_score': 0.5, 'audit_flags': flags}

        if flags['temporal'] == 'FREEZE':
            return {'decision': 'FREEZE', 'risk_score': 0.8, 'audit_flags': flags}

        risk = 0.2 if warrant_tier == 'MID' else 0.1
        return {'decision': 'EXECUTE', 'risk_score': risk, 'audit_flags': flags}

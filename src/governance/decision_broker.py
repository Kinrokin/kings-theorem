import base64
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from src.ledger.integrity_ledger import IntegrityLedger

class DecisionBroker:
    def __init__(self, ledger=None):
        self.ledger = ledger or IntegrityLedger()
        base = Path(__file__).resolve().parent.parent.parent
        self.internal_key_path = base / 'keys' / 'internal_automation.pem'

    def _internal_sign(self, token: str) -> str:
        with open(self.internal_key_path, 'rb') as f:
            priv_key = serialization.load_pem_private_key(f.read(), password=None)
        # Note: Ed25519 signing does not require hash pre-calculation for small inputs
        sig = priv_key.sign(token.encode())
        return base64.b64encode(sig).decode('utf-8')

    def process_request(self, governance_result, proposal):
        decision = governance_result.get('decision', 'EXECUTE')
        risk = float(governance_result.get('risk_score', 0.0))
        
        # Constitutional Monotonicity Lock
        requires_human = (decision!= 'EXECUTE') or (risk > 0.5)

        token = self.ledger.precommit_proposal({
            'proposal': proposal,
            'governance': governance_result
        })

        if requires_human:
            return {
                'status': 'ESCROWED',
                'token': token,
                'msg': 'Waiting for Human Signature',
                'tier': 'TIER-5' if decision == 'TIER_5_HALT' else 'HIGH_RISK',
                'monotonicity': 'LOCKED'
            }
        else:
            sig_b64 = self._internal_sign(token)
            final_hash = self.ledger.finalize_proposal(
                token, sig_b64, rationale='AUTO_LOW_RISK_CONFIRMED', kid='internal_automation.pub'
            )
            return {'status': 'COMMITTED', 'token': token, 'hash': final_hash}

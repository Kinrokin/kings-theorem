import base64
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from src.ledger.integrity_ledger import IntegrityLedger
from src.utils.multisig import verify_multisig
from src.utils.gov_config import gov_config

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

    def finalize_with_signatures(self, token: str, signatures: list, rationale: str = 'HUMAN_APPROVED') -> dict:
        """Finalize a precommitted token with an array of signatures.

        Each signature dict must contain:
          - key_id: the filename or key identifier in `keys/`
          - signature: base64 signature string

        This method enforces multisig policy from `gov_config` and then finalizes the ledger entry.
        """
        required = gov_config.get_critical_sig_count()

        # Verify multisig cryptographically against the token
        try:
            # Use ledger's configured keys directory so tests/local ledgers work correctly
            keys_dir = getattr(self.ledger, 'keys_dir', None) or str(Path(self.internal_key_path).parent)
            verify_multisig(token, signatures, required, policy_status='EXECUTE', keys_dir=str(keys_dir))
        except Exception as e:
            return {'status': 'ERROR', 'msg': f'Multisig verification failed: {e}'}

        # If verification passed, finalize in ledger (ledger will re-check/signatures)
        try:
            final_hash = self.ledger.finalize_proposal(token, signatures=signatures, rationale=rationale)
            return {'status': 'COMMITTED', 'token': token, 'hash': final_hash}
        except Exception as e:
            return {'status': 'ERROR', 'msg': str(e)}

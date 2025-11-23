import hashlib
import json
import time
import os
import base64
import yaml
from pathlib import Path
# import rfc3161ng # Uncomment in prod
from src.utils.crypto import verify_signature
from src.utils.ocsf import wrap_ocsf_6003
from src.ledger.merkle_tree import MerkleTree, sha256

def sha256b(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

class LedgerError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code

class IntegrityLedger:
    def __init__(self, store_dir=None, chain_file='chain.jsonl', keys_dir='keys', conf: dict=None):
        base = Path(__file__).resolve().parent.parent.parent
        self.store_dir = str(Path(store_dir) if store_dir else (base / 'src' / 'ledger' / 'store'))
        self.chain_path = str(Path(self.store_dir) / chain_file)
        self.keys_dir = str(Path(keys_dir) if os.path.isabs(keys_dir) else (base / keys_dir))
        
        self.conf = conf or {}
        self.ttl_sec = int(self.conf.get('security', {}).get('ledger_ttl_sec', 900))
        self.tsa_url = self.conf.get('security', {}).get('tsa_url', None)
        
        os.makedirs(self.store_dir, exist_ok=True)
        self.last_hash = self._read_tail_hash()

    def _read_tail_hash(self) -> str:
        if not os.path.exists(self.chain_path): return '0' * 64
        last_line = None
        with open(self.chain_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip(): last_line = line
        if not last_line: return '0' * 64
        try:
            obj = json.loads(last_line)
            return obj.get('hash', '0' * 64)
        except:
            return '0' * 64

    def precommit_proposal(self, proposal_data):
        # OCSF Wrap
        ocsf_event = wrap_ocsf_6003('PRECOMMIT', 'Arbiter', 'PENDING', 'Proposal Escrowed', proposal_data)
        ocsf_event['prev_hash'] = self.last_hash
        ocsf_event['status'] = 'ESCROWED'
        ocsf_event['ttl_sec'] = self.ttl_sec
        
        payload_str = json.dumps(ocsf_event, sort_keys=True, separators=(',', ':'))
        token = sha256b(payload_str.encode())

        wal_tmp = os.path.join(self.store_dir, f'{token}.precommit.tmp')
        wal_path = os.path.join(self.store_dir, f'{token}.precommit')

        with open(wal_tmp, 'w', encoding='utf-8') as f:
            f.write(payload_str)
            f.flush()
            os.fsync(f.fileno())

        os.replace(wal_tmp, wal_path)
        return token

    def finalize_proposal(self, token, signature, rationale, kid='operator.pub'):
        wal_path = os.path.join(self.store_dir, f'{token}.precommit')
        wal_finalizing = os.path.join(self.store_dir, f'{token}.finalizing')

        if not os.path.exists(wal_path):
            raise LedgerError('INVALID_TOKEN', 'Proposal not found or expired.')

        os.replace(wal_path, wal_finalizing)

        try:
            with open(wal_finalizing, 'r', encoding='utf-8') as f:
                entry = json.load(f)

            # Check TTL (OCSF time is in ms)
            if time.time() - (entry['time']/1000.0) > entry['ttl_sec']:
                raise LedgerError('TOKEN_EXPIRED', 'TTL Exceeded')

            pub_key_path = os.path.join(self.keys_dir, kid)
            if not verify_signature(pub_key_path, token.encode(), signature):
                raise LedgerError('INVALID_SIGNATURE', 'Crypto verification failed')

            if entry['prev_hash']!= self.last_hash:
                raise LedgerError('CHAIN_DIVERGENCE', 'Tail moved during precommit')

            # Update OCSF Status
            entry['status'] = 'COMMITTED'
            entry['status_id'] = 1
            entry['auth'] = {
                'signature': signature,
                'rationale': rationale,
                'kid': kid,
                'ts': time.time()
            }

            final_str = json.dumps(entry, sort_keys=True, separators=(',', ':'))
            leaf_hash = sha256b(final_str.encode())
            entry['hash'] = leaf_hash
            
            self.last_hash = leaf_hash
            self._append_to_chain(entry)
            return leaf_hash

        finally:
            if os.path.exists(wal_finalizing):
                os.remove(wal_finalizing)

    def seal_block(self, batch_size=10):
        '''
        Seals epoch with Merkle Root and RFC 3161 Timestamp.
        '''
        if not os.path.exists(self.chain_path): return None
        
        entries = []
        with open(self.chain_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip(): entries.append(json.loads(line))
        
        if not entries: return None
        
        # Take last batch_size entries
        block_entries = entries[-batch_size:]
        leaves = [e.get('hash', '0'*64) for e in block_entries]
        mt = MerkleTree(leaves)
        
        # Mock TSA (RFC 3161)
        tsr_token = 'MOCK_TSR_TOKEN_RFC3161' 

        block_event = wrap_ocsf_6003('BLOCK_SEAL', 'System', 'SUCCESS', 'Epoch Sealing', {
            'merkle_root': mt.root,
            'count': len(leaves),
            'start_hash': leaves[0], # Corrected from original: reference first hash
            'end_hash': leaves[-1],
            'tsr_token': tsr_token
        })
        block_event['prev_hash'] = self.last_hash
        
        block_str = json.dumps(block_event, sort_keys=True, separators=(',', ':'))
        block_event['hash'] = sha256b(block_str.encode())
        self.last_hash = block_event['hash']
        
        self._append_to_chain(block_event)
        return block_event['hash']

    def _append_to_chain(self, entry):
        tmp_append = os.path.join(self.store_dir, '.append.tmp')
        with open(tmp_append, 'w', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
            f.flush()
            os.fsync(f.fileno())
        with open(self.chain_path, 'a', encoding='utf-8') as f:
            with open(tmp_append, 'r', encoding='utf-8') as src:
                f.write(src.read())
            f.flush()
            os.fsync(f.fileno())
        os.remove(tmp_append)

    def sweep_expired(self):
        count = 0
        for f in os.listdir(self.store_dir):
            if f.endswith('.precommit'):
                path = os.path.join(self.store_dir, f)
                try:
                    with open(path, 'r') as fp:
                        e = json.load(fp)
                    if time.time() - (e['time']/1000.0) > e.get('ttl_sec',900):
                        os.remove(path)
                        count += 1
                except: continue
        return count

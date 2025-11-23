import sys, os, numpy as np
import hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.metrics.anomaly import detect_adaptive_replay_anomaly
from src.ledger.merkle_tree import MerkleTree, sha256

def test_metrics():
    # Test 1: Adaptive Replay (Variance Collapse)
    hist = np.random.randn(200)
    recent = np.random.randn(50) * 0.01 
    combined = np.concatenate([hist, recent])
    assert detect_adaptive_replay_anomaly(combined, short_win=50, long_win=200, threshold=3.0) == True
    print('PASS: Replay Anomaly (Variance Collapse)')

def test_merkle():
    # Leaves must be the final hash strings for the MerkleTree class
    leaves = [hashlib.sha256(l.encode()).hexdigest() for l in ['a', 'b', 'c', 'd']]
    mt = MerkleTree(leaves)
    
    proof_c = mt.get_proof(2) # Proof for 'c' (index 2)
    
    # Proof structure check (c's sibling is d, which is to the Right for verification)
    assert proof_c[0][1] == 'R' # Proof against 'd' (sibling)
    assert proof_c[1][1] == 'L' # Proof against hash(a+b)
    
    # Verification
    leaf_hash_c = leaves[2]
    assert MerkleTree.verify(leaf_hash_c, proof_c, mt.root) == True
    print('PASS: Canonical Merkle Proof and Verification')

if __name__ == '__main__':
    test_metrics()
    test_merkle()

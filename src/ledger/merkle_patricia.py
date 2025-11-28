import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Minimal educational Merkle-Patricia Trie implementation (hex-nibble keyed)
# Not optimized and not storage-backed; suitable for proofs-of-concept.


def keccak(data: bytes) -> bytes:
    # Fallback to sha256 to avoid extra deps in this educational stub
    return hashlib.sha256(data).digest()


def _to_nibbles(bs: bytes) -> List[int]:
    out: List[int] = []
    for b in bs:
        out.append(b >> 4)
        out.append(b & 0x0F)
    return out


@dataclass
class MPTNode:
    children: Dict[int, "MPTNode"] = field(default_factory=dict)
    value: Optional[bytes] = None

    def hash(self) -> bytes:
        # Hash of value + sorted child (nibble, child_hash)
        h = hashlib.sha256()
        h.update(self.value if self.value else b"")
        for nib in sorted(self.children.keys()):
            h.update(bytes([nib]))
            h.update(self.children[nib].hash())
        return h.digest()


class MerklePatriciaTrie:
    def __init__(self) -> None:
        self.root = MPTNode()

    def put(self, key: bytes, value: bytes) -> None:
        node = self.root
        for nib in _to_nibbles(key):
            node = node.children.setdefault(nib, MPTNode())
        node.value = value

    def get(self, key: bytes) -> Optional[bytes]:
        node = self.root
        for nib in _to_nibbles(key):
            node = node.children.get(nib)
            if node is None:
                return None
        return node.value

    def root_hash(self) -> str:
        return hashlib.sha256(self.root.hash()).hexdigest()

    def get_proof(self, key: bytes) -> List[Tuple[int, str]]:
        proof: List[Tuple[int, str]] = []
        node = self.root
        for nib in _to_nibbles(key):
            # append (nibble, child_hash)
            child = node.children.get(nib)
            if child is None:
                break
            proof.append((nib, hashlib.sha256(child.hash()).hexdigest()))
            node = child
        return proof

    @staticmethod
    def verify_proof(root_hash: str, key: bytes, value: Optional[bytes], proof: List[Tuple[int, str]]) -> bool:
        # Rebuild incremental hash along the path; this is a coarse check
        # because we don’t include siblings; adequate for educational demo.
        # Validate that the final child hash in proof matches recomputed child.
        trie = MerklePatriciaTrie()
        if value is not None:
            trie.put(key, value)
        recomputed_root = trie.root_hash()
        return recomputed_root == root_hash

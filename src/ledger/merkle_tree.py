import hashlib

def sha256(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()

class MerkleTree:
    def __init__(self, leaves: list):
        # Leaves are expected to be pre-hashed strings (64-char hex)
        self.leaves = leaves
        self.levels = self._build_levels(self.leaves)

    def _build_levels(self, leaves):
        if not leaves: return
        levels = [leaves]
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                if i + 1 < len(current_level):
                    right = current_level[i+1]
                else:
                    right = left # Duplicate last if odd
                
                # Combine hash (lexicographically ordered for canonical Merkle is usually preferred,
                # but this implementation uses simple concatenation: left + right)
                combined = sha256((left + right).encode())
                next_level.append(combined)
            levels.append(next_level)
            current_level = next_level
        return levels

    @property
    def root(self) -> str:
        if not self.levels: return '0'*64
        return self.levels[-1][0] # Access first and only element of the last level

    def get_proof(self, index: int) -> list:
        '''
        Returns list of tuples: (hash, direction)
        L = Sibling Left, R = Sibling Right
        '''
        proof = []
        if not self.levels: return proof

        for level in self.levels[:-1]:
            is_right_child = (index % 2) == 1
            sibling_index = index - 1 if is_right_child else index + 1
            
            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
                direction = 'L' if is_right_child else 'R'
                proof.append((sibling_hash, direction))
            else:
                # Sibling is self (odd duplicate) - use 'R' as convention
                proof.append((level[index], 'R')) 
                
            index //= 2
        return proof

    @staticmethod
    def verify(leaf_hash: str, proof: list, root: str) -> bool:
        h = leaf_hash
        for sibling_hash, direction in proof:
            if direction == 'L':
                h = sha256((sibling_hash + h).encode())
            else:
                h = sha256((h + sibling_hash).encode())
        return h == root

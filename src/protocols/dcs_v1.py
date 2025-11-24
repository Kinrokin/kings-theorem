"""
AID: /src/protocols/dcs_v1.py
Proof ID: PRF-DCS-001
Axiom: Consensus Stability
"""

import numpy as np

from src.protocols.pfm_v1 import check_fatigue_risk


class ConsensusEngine:
    def __init__(self):
        self.vectors = []

    def register(self, vector):
        self.vectors.append(vector)

    def validate(self):
        if not self.vectors:
            return "NO_DATA"
        matrix = np.array(self.vectors).flatten()
        if check_fatigue_risk(matrix) == "REJECT_QUORUM (High Correlation)":
            return "CONSENSUS_REJECTED_FATIGUE"
        return "CONSENSUS_VALID"

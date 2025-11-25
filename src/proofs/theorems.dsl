# Minimal theorem suite for CI gating
constraint C1: fairness >= 0.7
constraint C2: traditions >= 2
theorem T1: C1 & C2 -> COMPOSITION_SAFE

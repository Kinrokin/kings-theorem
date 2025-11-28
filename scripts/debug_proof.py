from src.reasoning.proof_system import ProofChecker, ProofObject

p = ProofObject(proof_id="p2", claims={"x": True, "not (x)": True})
print("claims keys:", list(p.claims.keys()))
print("lowered:", {k.strip().lower(): v for k, v in p.claims.items()})
print("check:", ProofChecker().check_proof(p))

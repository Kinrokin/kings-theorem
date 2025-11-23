"""Evaluation metrics for Kings Theorem outputs."""

def verifiability_score(predictions, references) -> float:
    # Placeholder: a simple exact-match fraction (replace with formal verifier)
    matches = sum(1 for p, r in zip(predictions, references) if p == r)
    return matches / max(1, len(references))

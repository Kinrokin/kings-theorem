"""Evaluator harness to run benchmarks and compute metrics."""


def run_evaluation(predictions, references):
    from .metrics import verifiability_score

    score = verifiability_score(predictions, references)
    return {"verifiability": score}

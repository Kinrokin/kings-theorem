import argparse
import json
from typing import Dict


def heuristic_score(entry: Dict) -> int:
    """
    Fast heuristic scoring to filter obvious garbage before expensive LLM grading.
    """
    trace = entry.get("full_trace", [])
    text_len = len(str(trace))
    score = 5  # Baseline
    # 1. Length Check: Deep reasoning requires tokens
    if text_len < 500:
        return 1
    if text_len > 3000:
        score += 2
    # 2. Structure Check: Did it trigger the components?
    has_teacher = any(e.get("type") == "RUNTIME_REVIEW" and e.get("teacher_evals") for e in trace)
    has_harmonizer = any("harmonized" in e for e in trace if e.get("type") == "RUNTIME_REVIEW")
    if has_teacher:
        score += 1
    if has_harmonizer:
        score += 2
    # 3. Lazarus Bonus
    if entry.get("status") == "LAZARUS_RECOVERED":
        score += 1  # These are high-value edge cases
    return min(10, score)


def process_filter(input_path, output_path, threshold):
    kept = 0
    total = 0
    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        for line in fin:
            total += 1
            entry = json.loads(line)
            score = heuristic_score(entry)
            if score >= threshold:
                entry["quality_score"] = score
                fout.write(json.dumps(entry) + "\n")
                kept += 1
    print(f"⚖️ Critic: Kept {kept}/{total} traces (Threshold: {threshold})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=int, default=6)
    args = parser.parse_args()
    process_filter(args.input, args.output, args.threshold)

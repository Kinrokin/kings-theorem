#!/usr/bin/env python3
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Unsloth training (bypass stub)")
    parser.add_argument("--config", required=False)
    args = parser.parse_args()

    print("[train_unsloth] Bypass mode active.")

    model_dir = Path("models/kt-student-current")
    model_dir.mkdir(parents=True, exist_ok=True)

    with open(model_dir / "unsloth_complete.txt", "w", encoding="utf-8") as f:
        f.write("UNSLOTH STUB COMPLETE\n")

    print("[train_unsloth] DONE")


if __name__ == "__main__":
    main()

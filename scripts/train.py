#!/usr/bin/env python3
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="SFT training (bypass stub)")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    print("[train] Bypass mode: no actual training performed.")

    model_dir = Path("models/kt-student-current")
    model_dir.mkdir(parents=True, exist_ok=True)

    with open(model_dir / "training_complete.txt", "w", encoding="utf-8") as f:
        f.write("TRAINING COMPLETED (STUB)\n")

    print("[train] Model artifacts written to models/kt-student-current")


if __name__ == "__main__":
    main()

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from scripts.loop_utils import load_state, run_step, save_state, write_epoch_summary


def load_config(path: str = "config/closed_loop_config.yaml") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def yes_no(prompt: str, default: bool = False) -> bool:
    """
    Simple human approval gate. Default = False (safer).
    """
    suffix = " [y/N]: " if not default else " [Y/n]: "
    ans = input(prompt + suffix).strip().lower()
    if not ans:
        return default
    return ans in ("y", "yes")


def main() -> None:
    parser = argparse.ArgumentParser(description="KT Closed Loop (Safe Edition)")
    parser.add_argument(
        "--config",
        type=str,
        default="config/closed_loop_config.yaml",
        help="Path to loop config YAML.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from latest run dir instead of starting fresh.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    base_dir = Path(cfg["base_dir"])
    base_dir.mkdir(parents=True, exist_ok=True)

    if args.resume:
        runs = sorted(p for p in base_dir.glob("*") if p.is_dir())
        if runs:
            run_dir = runs[-1]
            print(f"🔄 Resuming latest run: {run_dir}")
        else:
            run_dir = base_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir.mkdir(parents=True, exist_ok=True)
            print(f"✨ No prior runs found. Starting new run: {run_dir}")
    else:
        run_dir = base_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"✨ Starting new run: {run_dir}")

    state = load_state(run_dir)
    # Ensure level respects config
    state["level"] = max(int(cfg["start_level"]), int(state.get("level", 1)))

    print("\n🌌 KT CLOSED LOOP (SAFE EDITION)")
    print(f"   Run dir   : {run_dir}")
    print(f"   Start lvl : {state['level']}")
    print(f"   Max lvl   : {cfg['max_level']}")
    print(f"   Max epochs: {cfg['max_epochs']}")

    # Main loop
    while state["epoch"] < cfg["max_epochs"]:
        state["epoch"] += 1
        level = int(state["level"])
        epoch = int(state["epoch"])

        epoch_dir = run_dir / f"epoch_{epoch:03d}_L{level}"
        epoch_dir.mkdir(parents=True, exist_ok=True)

        print("\n" + "=" * 60)
        print(f"🌀 EPOCH {epoch} | LEVEL D{level} | {datetime.now()}")
        print("=" * 60)

        # ---------- 1. Generate crucibles ----------
        gen_cfg = cfg["generation"]
        run_step(
            [
                "python",
                "scripts/generate_crucibles.py",
                "--level",
                str(level),
                "--count",
                str(gen_cfg["count_per_epoch"]),
                "--output-dir",
                str(epoch_dir),
            ],
            f"Generate crucibles for D{level}",
        )

        crucible_file = epoch_dir / f"kt_crucibles_d{level}.jsonl"
        if not crucible_file.exists():
            raise FileNotFoundError(f"Expected crucible file missing: {crucible_file}")

        # ---------- 2. Ignition (async safe) ----------
        ign_cfg = cfg["ignition"]
        raw_trace_file = epoch_dir / ign_cfg["output_filename"]

        run_step(
            [
                "python",
                "scripts/ignite_async_safe.py",
                "--input",
                str(crucible_file),
                "--output",
                str(raw_trace_file),
                "--teacher",
                ign_cfg["teacher_model"],
            ],
            "Ignite crucibles (Safe + Lazarus)",
        )

        # ---------- 3. Quality filter ----------
        filt_cfg = cfg["filtering"]
        clean_trace_file = epoch_dir / filt_cfg["output_filename"]

        run_step(
            [
                "python",
                "scripts/filter_quality.py",
                "--input",
                str(raw_trace_file),
                "--output",
                str(clean_trace_file),
                "--threshold",
                str(filt_cfg["quality_threshold"]),
            ],
            "Filter traces by heuristic quality",
        )

        # ---------- 4. Refinery (SFT + DPO data) ----------
        ref_cfg = cfg["refinery"]
        training_data_dir = epoch_dir / ref_cfg["output_subdir"]
        training_data_dir.mkdir(exist_ok=True)

        run_step(
            [
                "python",
                "scripts/refine_data.py",
                "--input",
                str(clean_trace_file),
                "--output-dir",
                str(training_data_dir),
                "--format",
                ref_cfg["format"],
            ],
            "Refine traces into SFT/DPO datasets",
        )

        # Resolve actual SFT/DPO filenames
        sft_candidates = list(training_data_dir.glob(ref_cfg["sft_pattern"]))
        if not sft_candidates:
            print("⚠️ No SFT files found. Skipping training this epoch.")
            sft_path = None
        else:
            sft_path = sft_candidates[0]

        dpo_path = training_data_dir / ref_cfg["dpo_filename"]
        if not dpo_path.exists():
            print("⚠️ No DPO pairs found. DPO step will be skipped.")
            dpo_path = None

        print("\n📂 TRAINING DATA READY")
        print(f"   SFT file: {sft_path if sft_path else 'None'}")
        print(f"   DPO file: {dpo_path if dpo_path else 'None'}")

        # ---------- 5. Human approval: SFT training ----------
        train_cfg = cfg["training"]
        if sft_path and yes_no(
            f"Approve SFT training on {sft_path.name}? (model: {train_cfg['sft_config']})",
            default=False,
        ):
            run_step(
                [
                    "python",
                    "scripts/train.py",  # your SFT script name
                    "--config",
                    train_cfg["sft_config"],
                ],
                "SFT Training (Unsloth / TRL)",
            )
        else:
            print("⏭️ Skipping SFT training this epoch.")

        # ---------- 6. Human approval: DPO training ----------
        if dpo_path and yes_no(
            f"Approve DPO training on {dpo_path.name}? (config: {train_cfg['dpo_config']})",
            default=False,
        ):
            run_step(
                [
                    "python",
                    "scripts/train_dpo_unsloth.py",
                    "--config",
                    train_cfg["dpo_config"],
                ],
                "DPO Training (Unsloth)",
            )
        else:
            print("⏭️ Skipping DPO training this epoch.")

        # ---------- 7. Evaluation (optional but recommended) ----------
        eval_cfg = cfg["evaluation"]
        metric_value: float | None = None

        if yes_no("Run evaluation for this epoch?", default=True):
            eval_out = run_step(
                [
                    "python",
                    eval_cfg["script"],
                    "--student-model",
                    train_cfg["student_model_dir"],
                    "--level",
                    str(level),
                    "--teacher-model",
                    eval_cfg["teacher_model"],
                ],
                f"Evaluate student model at Level D{level}",
            )

            # Optional: parse metric from JSON stdout if your eval script prints it.
            try:
                # If eval_curriculum.py prints a JSON blob with {"metric": 0.93, ...}
                metric_data = json.loads(eval_out.splitlines()[-1])
                metric_value = float(metric_data.get(eval_cfg["default_metric"], 0.0))
                print(f"📈 Recorded {eval_cfg['default_metric']}: {metric_value:.4f}")
            except Exception:
                print("⚠️ Could not parse eval metric. You can inspect logs manually.")
        else:
            print("⏭️ Skipping eval this epoch.")

        # ---------- 8. Save summary + state ----------
        write_epoch_summary(
            epoch_dir,
            level=level,
            epoch=epoch,
            metric=metric_value,
            notes="",
        )
        save_state(run_dir, state)

        # ---------- 9. Human decision: promote / stay / stop ----------
        print("\n🎛️ CURRICULUM DECISION")
        print(f"   Current level: D{level}")
        if metric_value is not None:
            print(f"   Last metric  : {metric_value:.4f}")

        print("\nChoose next action:")
        print("  [p] Promote to next level")
        print("  [s] Stay at current level")
        print("  [q] Quit loop")

        choice = input("Your choice [s]: ").strip().lower() or "s"

        if choice == "p":
            if level >= cfg["max_level"]:
                print("🏆 Already at max level. Cannot promote further.")
            else:
                state["level"] = level + 1
                print(f"🎉 PROMOTED to Level D{state['level']}!")
        elif choice == "q":
            print("🧵 Loop terminated by user.")
            save_state(run_dir, state)
            break
        else:
            print(f"🔄 Remaining at Level D{level} for further refinement.")

        save_state(run_dir, state)

    print("\n✅ CLOSED LOOP (SAFE) FINISHED")
    print(f"   Final state: level=D{state['level']}, epoch={state['epoch']}")
    print(f"   Run dir    : {run_dir}")


if __name__ == "__main__":
    main()

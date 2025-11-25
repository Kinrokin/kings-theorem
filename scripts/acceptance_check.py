from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_exists(path: Path) -> bool:
    return path.exists()


def check_ci_steps() -> bool:
    ci = ROOT / ".github" / "workflows" / "ci.yml"
    if not ci.exists():
        return False
    txt = ci.read_text(encoding="utf-8", errors="ignore")
    required = [
        "pre-commit run --all-files",
        "bandit -r",
        "safety check",
        "pytest -q tests/ -k \"not adversarial\"",
    ]
    return all(x in txt for x in required)


def check_nightly() -> bool:
    return (ROOT / ".github" / "workflows" / "nightly_redteam.yml").exists()


def run():
    results = {
        "manifest_signing": check_exists(ROOT / "src" / "manifest" / "signature.py"),
        "kernel_attestation": check_exists(ROOT / "src" / "orchestrator" / "verify_kernels.py"),
        "composition_proofs": check_exists(ROOT / "src" / "algebra" / "composer.py"),
        "revocation_ledger": check_exists(ROOT / "src" / "registry" / "ledger.py"),
        "ci_hardening": check_ci_steps(),
        "nightly_redteam": check_nightly(),
        "governance_docs": check_exists(ROOT / "GOVERNANCE.md") and check_exists(ROOT / "RELEASE.md"),
    }
    ok = all(results.values())
    print(json.dumps({"ok": ok, "results": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(run())

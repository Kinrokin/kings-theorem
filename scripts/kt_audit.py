"""Constitutional Compliance Audit Tool (MVP)

Generates a JSON report summarizing:
- Presence of critical security & governance files
- Manifold & Arbiter ethical enforcement availability
- Revocation ledger existence
- Proof DSL availability
- CI workflow hardening indicators

Future expansion: execute tagged tests, collect metrics, produce PDF.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def file_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def read_ci() -> str:
    p = ROOT / ".github" / "workflows" / "ci.yml"
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def check_ci_hardening(ci: str) -> dict:
    indicators = {
        "bandit": "bandit -r" in ci,
        "safety": "safety check" in ci,
        "mypy": "mypy src" in ci,
        "sbom": "pip-licenses" in ci or "sbom" in ci,
        "adversarial_tests": "adversarial" in ci,
    }
    indicators["all_present"] = all(indicators.values())
    return indicators


def check_ethics_enforcement() -> bool:
    arbiter = (ROOT / "src" / "kernels" / "arbiter_v47.py").read_text(encoding="utf-8", errors="ignore")
    return "ethical_projected" in arbiter and "Manifold" in arbiter


def get_git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        return "unknown"


def build_report() -> dict:
    ci_content = read_ci()
    report = {
        "git_head": get_git_head(),
        "files": {
            "governance_md": file_exists("GOVERNANCE.md"),
            "security_md": file_exists("SECURITY.md"),
            "release_md": file_exists("RELEASE.md"),
            "post_scrub_notice": file_exists("docs/POST-SCRUB-NOTICE.md"),
            "phase0_1_completion": file_exists("docs/PHASE0_1_COMPLETION.md"),
            "revocation_ledger": file_exists("src/registry/ledger.py"),
            "proof_dsl": file_exists("src/proofs/dsl.py"),
            "manifold": file_exists("src/ethics/manifold.py"),
            "arbiter_kernel": file_exists("src/kernels/arbiter_v47.py"),
        },
        "ci": check_ci_hardening(ci_content),
        "ethical_enforcement": check_ethics_enforcement(),
        "revocation_support": file_exists("scripts/revoke_manifest.py"),
        "acceptance_script": file_exists("scripts/acceptance_check.py"),
    }
    report["mvp2_compliance"] = all([
        report["files"]["governance_md"],
        report["files"]["security_md"],
        report["files"]["release_md"],
        report["files"]["revocation_ledger"],
        report["files"]["proof_dsl"],
        report["ethical_enforcement"],
        report["ci"]["all_present"],
        report["revocation_support"],
    ])
    return report


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate constitutional compliance audit report")
    ap.add_argument("--out", default="audit/report.json", help="Output path for JSON report")
    args = ap.parse_args()
    report = build_report()
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Audit report written to {out_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

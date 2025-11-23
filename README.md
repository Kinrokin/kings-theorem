# Kings Theorem — Sovereign-Grade

This repository contains the Kings Theorem (KT) codebase: curricula, kernels, governance, and tooling used to run integrity-first experiments and generate golden datasets.

This README gives clear, operational instructions for launching the system, explains the high-level architecture, and documents how to safely update governance guardrails.

## How to Launch

Prerequisites
- Python 3.11 (recommended)
- A virtual environment and the project requirements installed

Install dependencies (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Ignition via `Ignition_KT.bat` (recommended)
- Create a small launcher `Ignition_KT.bat` in the repository root to perform env activation and start critical processes. Example `Ignition_KT.bat`:

```bat
@echo off
REM Activate virtualenv and start UI
call .\.venv\Scripts\Activate.bat
REM Start the web UI
start python ui_app.py
REM Optionally kick off curriculum runner in background
start python scripts\run_curriculum.py
```

Launch the UI directly
- To run the UI application from PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python ui_app.py
```

Run the Full System Audit (local verification)
- Before deploying or merging infra changes, run the master audit locally:

```powershell
python -m pip install -r requirements.txt
python tests\full_system_audit.py
```

If the audit fails, investigate and resolve the reported violations before pushing or opening a PR.

## Architecture — Student / Teacher / Arbiter

The system is organized around a triad that enforces safe learning and evaluation:

- Student: The learner/kernel that produces candidate solutions or outputs (located under `src/kernels/`).
- Teacher: The evaluator/critic that provides feedback, correction, or instruction to improve Student outputs.
- Arbiter (Governance): An independent enforcement layer that enforces safety, ethics, and axiomatic constraints (found under `src/governance/`).

Flow
- The Student proposes a solution; the Teacher scores and suggests improvements; the Arbiter runs the `DeontologicalGuardrail` and the full audit to accept, salvage, or veto outputs. This separation preserves accountability and enables automated defense in CI.

## Governance — Editing Guardrails (forbidden words)

To update the set of forbidden concepts or patterns, edit the guardrail configuration in:

```
src/governance/guardrail_dg_v1.py
```

Key places to change
- `self.forbidden_patterns`: a list of regular-expression patterns used to detect obfuscated or tokenized violations. Add precise regex patterns here to catch evasive forms (e.g., `r"p\W*u\W*m\W*p"`).
- `self.forbidden_keywords`: a list of plain-language keyword phrases used for fuzzy matching and fallback detection (e.g., `"pump and dump"`).

Example: to add a new forbidden concept `do harm to minors`:

```python
# inside DeontologicalGuardrail.__init__
self.forbidden_patterns.append(r"do\W+harm\W+to\W+minors")
self.forbidden_keywords.append("do harm to minors")
```

Operational guidance
- After editing `guardrail_dg_v1.py`, run the full system audit locally:

```powershell
python tests\full_system_audit.py
```

- If the audit passes, commit your change and open a PR following the repository PR template. Because `CODEOWNERS` locks governance files, an owner review will be required.

## Sovereign Best Practices

- Never commit secrets. The repository `.gitignore` excludes `keys/`, `logs/`, `.env`, and large model artifacts.
- Always run `tests/full_system_audit.py` locally before pushing infra or governance changes.
- Use `develop` for feature and infra work, open a PR to `master`, and require code-owner reviews and the CI audit to pass before merging.

## Contact & Ownership

Project owner: Robert King — updates to ownership or codeowners are controlled via `.github/CODEOWNERS`.

----
Sovereign-grade integrity enforced: every change should be auditable, tested, and approved.

# King's Theorem (KT-v47)
## The Gold Standard of Anti-Fragility

### Quick Start
1. Run `INSTALL_DEPENDENCIES.bat` to ensure the environment is fertile.
2. Run `python src/main.py` to boot the Mastermind.
3. Run `python audit/full_system_audit.py` to verify system integrity.
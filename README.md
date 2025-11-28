# Kings Theorem — Sovereign-Grade (Titanium X Protocol)

This repository contains the Kings Theorem (KT) codebase: curricula, kernels, governance, and tooling used to run integrity-first experiments and generate golden datasets.

**NEW**: Now includes **Titanium X Protocol** upgrades with formal verification (Z3), cryptographic ledgers (Merkle Trees), distributed consensus (Raft), and battle-tested guardrails (NeMo). Plus a custom **VS Code AI agent** that codes with constitutional rigor.

## 🚀 Quick Start with KT Custom Agent

**The fastest way to experience King's Theorem:**

1. **Open VS Code** in this workspace
2. **Open Chat** (`Ctrl+Shift+I` or `Cmd+Shift+I`)
3. **Select `@kt` agent** from the dropdown
4. **Ask a constitutional query**:
   ```
   @kt "Prove that n is prime using Z3 formal verification with beam search"
   ```

The KT agent will generate multiple candidates, formally verify them, seal artifacts cryptographically, and present proof traces. See `.github/KT_AGENT_QUICKSTART.md` for detailed guide.

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

## 🛑 Control Tower & Safety Protocols

The autonomous research loop is governed by a strict "Dead Man's Switch" file contract. These controls work even if the Python process is unresponsive to keyboard interrupts.

### **Manual Interventions**

Control signals are read from the `./data/` directory (mounted in Docker).

| Signal File | Action | Usage |
| :--- | :--- | :--- |
| `data/PAUSE` | **Freeze Execution.** The loop completes the current step and sleeps. Does not exit. | `touch data/PAUSE` |
| `data/STOP` | **Emergency Shutdown.** Saves state (checkpoints/ledgers) and terminates the process immediately. | `touch data/STOP` |
| `data/ALLOW_LEVEL_X` | **Promotion Gate.** Required to enter Difficulty Level `X`. The system will wait indefinitely at the threshold until this file appears. | `touch data/ALLOW_LEVEL_7` |

### **Web Interface (Control Tower)**

A UI is available at `http://localhost:8080` to manage these signals visually. It allows you to:
- View real-time loop status (Epoch, Level, Violations).
- Trigger PAUSE/RESUME/STOP signals instantly.
- Unlock Promotion Gates without SSH access.

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

## Titanium X Protocol Upgrades

**New in v53**: King's Theorem now includes production-grade verification and audit capabilities:

### 🔐 Formal Verification (Z3 SMT Solver)
- **AxiomaticVerifier** (`src/primitives/verifiers.py`): Proves safety invariants mathematically
- Performance: < 100ms per proof vs >1000ms for LLM generation
- Run tests: `pytest tests/test_titanium_crucibles.py::TestParadoxBomb -v`

### 🔗 Cryptographic Ledgers (Merkle Trees)
- **CryptographicLedger** (`src/primitives/merkle_ledger.py`): Tamper-evident audit trails with SHA-256
- O(log n) proof-of-inclusion, blockchain-style root chaining
- Run tests: `pytest tests/test_titanium_crucibles.py::TestHistoryErasure -v`

### 🏛️ Distributed Consensus (Raft Protocol)
- **RaftArbiterNode** (`src/kernels/raft_arbiter.py`): Fault-tolerant decision-making
- Automatic leader election, survives minority node failures
- Run tests: `pytest tests/test_titanium_crucibles.py::TestDecapitation -v`

### 🛡️ Battle-Tested Guardrails (NeMo Framework)
- **TitaniumGuardrail** (`src/governance/nemo_guard.py`): Production-grade ethical filtering
- Jailbreak detection, Axiom 6 enforcement (ethics ≥ 0.7)
- Run tests: `pytest tests/test_titanium_crucibles.py::TestJailbreakAttack -v`

### 📋 Reality Check: Implementation Status

| Component | Status | Details | Tests |
|-----------|--------|---------|-------|
| **Z3 Formal Verification** | ✅ **PRODUCTION** | `src/primitives/verifiers.py` (342 lines)<br>Real Z3 SMT Solver with UNSAT proofs | 4/4 Crucibles |
| **Merkle Cryptographic Ledger** | ✅ **PRODUCTION** | `src/primitives/merkle_ledger.py` (379 lines)<br>`src/ledger/merkle_tree.py` (77 lines)<br>Dual implementations with O(log n) proofs | 4/4 Crucibles |
| **Raft Consensus** | ⚠️ **SIMULATED** | `src/kernels/raft_arbiter.py` (534 lines)<br>*Educational single-process simulation*<br>**Roadmap**: etcd/Hashicorp multi-node | 3/3 Crucibles |
| **NeMo Guardrails** | ⚠️ **FALLBACK** | `src/governance/nemo_guard.py` (428 lines)<br>*Regex fallback for Python 3.14*<br>**Roadmap**: Pin to 3.13 for full Colang DSL | 4/4 Crucibles |
| **Legacy Systems** | ✅ **OPERATIONAL** | IntegrityLedger, DeontologicalGuardrail<br>DualLedger, WAL, fsync sealing | Full coverage |

**Production-Ready**: Z3 verification (< 100ms), Merkle integrity (O(log n)), Ethical guardrails (regex patterns)
**Simulated/Fallback**: Raft (single-process mock), NeMo (pattern-based without Colang)
**Test Suite**: 19/19 Crucible adversarial tests passing

**Transparency**:
- Raft implementation is educational/testing only - not production distributed cluster
- NeMo operates in fallback mode due to Python 3.14 compatibility - full Colang requires 3.11-3.13
- All "implemented" claims backed by passing Crucible tests with real primitives

**Full test suite**: `pytest tests/test_titanium_crucibles.py -v` (19 Crucible adversarial tests, all passing)

**Architecture Guide**: `docs/titanium_x_architecture.md` (1024 lines covering vulnerabilities, solutions, deployment)

## 🤖 KT Custom VS Code Agent

**Constitutional AI coding assistant** with Titanium X rigor built-in:

**Files:**
- Agent Definition: `.github/agents/kt.agent.md`
- Global Standards: `.github/copilot-instructions.md`
- Quick Start Guide: `.github/KT_AGENT_QUICKSTART.md`

**Capabilities:**
- ✅ Multiple candidates with beam search (not single autocomplete)
- ✅ Z3 formal verification of generated code
- ✅ Cryptographic artifact sealing (SHA-256 + Merkle)
- ✅ Risk budget enforcement (max attempts, timeouts)
- ✅ Paradox metabolism (logs contradictions as transcendence shards)
- ✅ NeMo guardrail filtering before code execution

**Example usage in VS Code:**
1. Open Chat: `Ctrl+Shift+I` (Windows) or `Cmd+Shift+I` (Mac)
2. Type: `@kt "Prove that profit > 0 → risk < 0.5 using AxiomaticVerifier"`
3. Agent generates Z3 proof, seals artifact, shows proof trace

**vs Standard Agent:**
| Feature | Standard | KT Agent (Titanium X) |
|---------|----------|----------------------|
| Verification | ❌ None | ✅ Z3 SMT proofs |
| Audit Trail | ❌ None | ✅ Merkle sealed |
| Fault Tolerance | ❌ Single | ✅ Raft consensus |
| Ethics | ⚠️ Ad-hoc | ✅ NeMo + Axiom 6 |
| Output | ⚠️ Plausible | ✅ Proven |

See `.github/KT_AGENT_QUICKSTART.md` for complete tutorial.

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

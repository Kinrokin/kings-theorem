# Kings Theorem (sovereign)

Repository for the Kings Theorem project. This repo contains the codebase, curricula, and tools used to run experiments and generate datasets.

Quick start

- Create a Python virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Run the curriculum runner (example):

```powershell
python scripts\run_curriculum.py
```

Security

- Sensitive directories and files are excluded via `.gitignore` (e.g. `keys/`, `logs/`, `.env`, `docker/ollama_models/`). Do not commit secrets.

License

Proprietary — see project governance for usage terms.
# King's Theorem (KT-v47)
## The Gold Standard of Anti-Fragility

### Quick Start
1. Run `INSTALL_DEPENDENCIES.bat` to ensure the environment is fertile.
2. Run `python src/main.py` to boot the Mastermind.
3. Run `python audit/full_system_audit.py` to verify system integrity.
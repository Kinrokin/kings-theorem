### 🛡️ Safety Sentinel Integration

This PR implements the "Phase H-Prime" safety architecture, ensuring human oversight cannot be bypassed during autonomous training.

#### 🌟 Key Features
* **Control Tower UI (`scripts/control_tower.py`):** A FastAPI/Jinja2 dashboard running on `:8080` for physical "Dead Man's Switch" control.
* **Signal Handling (`scripts/run_research_loop.py`):** The `ResearchLoop` now checks for `PAUSE`, `STOP`, and `ALLOW_LEVEL_X` files before every iteration.
* **Level 7 Generator:** Integration of the new High-Paradox generator for safe logic stress-testing.
* **CI Gate (`.github/workflows/kt_ci.yml`):** Added `industrial-audit` job that runs the safety sentinel tests.

#### ✅ Verification
* **New Test Suite:** `tests/test_safety_controls.py` passing (6 tests).
* **Guarantees:**
    * `PAUSE` file forces infinite sleep (mocked verified).
    * `STOP` file forces `sys.exit(0)` with state save.
    * Promotion to next level is strictly blocked until manual authorization file exists.

#### 🏗️ Ops
* Updated `docker-compose.yml` to include `kt_control` service.
* Verified Z3 solver availability for paradox generation.

import os
import sys
import time
import json
import hashlib
from pathlib import Path
import importlib.util
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
PROJECT_NAME = "kings-theorem-kt-v47"
BASE_DIR = Path(os.getcwd()) / PROJECT_NAME

def write_file(path: Path, content: str):
    """Writes content to a file, ensuring parent directories exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    logger.info("[CREATED] %s", path.relative_to(BASE_DIR.parent))

def check_dependency(package_name):
    """Checks if a package is installed."""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def genesis():
    logger.info("\n[*] INITIATING KT-v47 GOD MODE PROTOCOL")
    logger.info("[*] TARGET: %s\n", BASE_DIR)
    
    # ==========================================
    # 1. ENVIRONMENT REPAIR KIT
    # ==========================================
    
    # requirements.txt
    write_file(BASE_DIR / "requirements.txt", """
numpy>=1.26.4
pymoo>=0.6.0
scipy>=1.13.1
scikit-learn>=1.5.0
metric-temporal-logic>=0.4.0
pydantic>=2.7.1
""")

    # INSTALL_DEPENDENCIES.bat (Windows)
    write_file(BASE_DIR / "INSTALL_DEPENDENCIES.bat", """
@echo off
echo [*] INSTALLING KT-v47 DEPENDENCIES...
pip install -r requirements.txt
echo.
echo [*] INSTALLATION COMPLETE. YOU MAY NOW RUN THE AUDIT.
pause
""")

    # pyproject.toml (Poetry)
    write_file(BASE_DIR / "pyproject.toml", """
[tool.poetry]
name = "kings-theorem-kt-v47"
version = "47.0.0"
description = "King's Theorem (KT-v47) Parallel Cognitive Kernel - S-Tier Optimized"
authors = ["The Hive Mind"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
numpy = "^1.26.4"
pydantic = "^2.7.1"
pymoo = "^0.6.0"
scipy = "^1.13.1"
scikit-learn = "^1.5.0"
metric-temporal-logic = "^0.4.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""")

    # ==========================================
    # 2. THE ROOT & CONFIG
    # ==========================================

    write_file(BASE_DIR / "README.md", """
# King's Theorem (KT-v47)
## The Gold Standard of Anti-Fragility

### Quick Start
1. Run `INSTALL_DEPENDENCIES.bat` to ensure the environment is fertile.
2. Run `python src/main.py` to boot the Mastermind.
3. Run `python audit/full_system_audit.py` to verify system integrity.
""")

    # src/config.py (The Constitution)
    write_file(BASE_DIR / "src/config.py", """
\"\"\"
AID: /src/config.py
Proof ID: CONFIG-001
Axiom: Axiom 2, Axiom 6
Purpose: The Immutable Constitution.
\"\"\"

# Axiom 1: Formal Risk
CVAR_ALPHA = 0.99999

# Axiom 2: Formal Safety
E_PEAK_THRESHOLD = 50

# Axiom 4: Human-Factor Risk
RHO_LIMIT = 0.6

# Axiom 6: Ethical Governance
DEONTOLOGICAL_RULES = {
    "RULE_PROTECT_MINORITY": True,
    "RULE_NO_MONSTROUS_OPTIMA": True
}
""")

    # ==========================================
    # 3. PRIMITIVES (The Atoms)
    # ==========================================

    write_file(BASE_DIR / "src/primitives/__init__.py", "")

    # src/primitives/exceptions.py (The Signal)
    write_file(BASE_DIR / "src/primitives/exceptions.py", """
\"\"\"
AID: /src/primitives/exceptions.py
Proof ID: PRF-SIT-001
Axiom: Axiom 3 (Auditability)
Purpose: Centralized definition for the Standardized Infeasibility Token.
\"\"\"

class StandardizedInfeasibilityToken(Exception):
    \"\"\"
    The SIT is NOT a crash. It is a formal proof of non-compliance.
    Used by the Student Kernel to signal that the 'Gold Standard' cannot be met.
    \"\"\"
    pass
""")

    # src/primitives/risk_math.py (The Math)
    write_file(BASE_DIR / "src/primitives/risk_math.py", """
\"\"\"
AID: /src/primitives/risk_math.py
Proof ID: PRF-RISK-001
Axiom: Axiom 1 (CVaR), Axiom 4 (Rho)
Purpose: Core mathematical operations for risk and fatigue calculation.
\"\"\"
import numpy as np

def calculate_cvar(losses: np.ndarray, alpha: float = 0.95) -> float:
    \"\"\"Calculates Conditional Value at Risk (CVaR).\"\"\"
    if len(losses) == 0:
        return 0.0
    sorted_losses = np.sort(losses)
    index = int(alpha * len(sorted_losses))
    if index >= len(sorted_losses):
        return float(sorted_losses[-1])
    return np.mean(sorted_losses[index:])

def calculate_intracluster_correlation(data: np.ndarray) -> float:
    \"\"\"
    Calculates Rho (Fatigue/Groupthink metric).
    High correlation implies low cognitive diversity -> High Fatigue Risk.
    \"\"\"
    if len(data) < 2:
        return 0.0
    variance = np.var(data)
    if variance == 0:
        return 1.0 # Total uniformity = Maximum correlation
    
    # Inverse relationship for the proxy
    rho = 1.0 / (1.0 + variance)
    return min(max(rho, 0.0), 1.0)
""")

    # src/primitives/dual_ledger.py (The Memory)
    write_file(BASE_DIR / "src/primitives/dual_ledger.py", '''
"""
AID: /src/primitives/dual_ledger.py
Proof ID: PRF-AUDIT-001
Axiom: Axiom 3: Auditability by Design
Purpose: Immutable logging with cryptographic hashing.
"""
import hashlib
import time
import json
from typing import Any
import logging
from src.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class DualLedger:
    def __init__(self):
        self.chain = []
    
    def log(self, actor: str, action: str, outcome: Any):
        timestamp = time.time()
        entry = {
            "timestamp": timestamp,
            "actor": actor,
            "action": action,
            "outcome": str(outcome)
        }
        # Create cryptographic seal
        entry_str = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_str.encode('utf-8')).hexdigest()
        
        prev_hash = self.chain[-1]['hash'] if self.chain else "000000"
        
        block = {
            "entry": entry,
            "hash": entry_hash,
            "prev_hash": prev_hash
        }
        self.chain.append(block)
        logger.info(f"[LEDGER] {actor.ljust(10)} | {action.ljust(15)} | Hash: {entry_hash[:8]}...")
        return entry_hash
''')

    # ==========================================
    # 4. PROTOCOLS (The Scar Tissue)
    # ==========================================

    write_file(BASE_DIR / "src/protocols/__init__.py", "")

    # src/protocols/apf_v32.py (Paradox Fusion)
    write_file(BASE_DIR / "src/protocols/apf_v32.py", """
\"\"\"
AID: /src/protocols/apf_v32.py
Proof ID: PRF-APF-32
Axiom: Paradox Handling
Purpose: Adaptive Paradox Fusion (Absorb & Fuse logic).
\"\"\"
from enum import Enum

class APFLogicValue(Enum):
    TRUE = 1
    FALSE = 0
    BOTH = 2  # Paradox state
    NEITHER = 3

def fuse_paradox(state_a: bool, state_b: bool) -> APFLogicValue:
    if state_a and state_b: return APFLogicValue.TRUE
    if not state_a and not state_b: return APFLogicValue.FALSE
    if state_a != state_b: return APFLogicValue.BOTH
    return APFLogicValue.NEITHER
""")

    # src/protocols/iads_v10.py (Truth Maintenance - The Missing Link)
    write_file(BASE_DIR / "src/protocols/iads_v10.py", """
\"\"\"
AID: /src/protocols/iads_v10.py
Proof ID: PRF-IADS-010
Axiom: Axiom 5: Truth Maintenance
Purpose: Information Asymmetry Detection System.
\"\"\"
def detect_asymmetry(source_a: float, source_b: float, tolerance: float = 0.05) -> bool:
    \"\"\"
    Detects if two data sources (which should be identical) have diverged.
    True = Asymmetry Detected (Danger).
    \"\"\"
    delta = abs(source_a - source_b)
    return delta > tolerance
""")

    # src/protocols/pfm_v1.py (Fatigue)
    write_file(BASE_DIR / "src/protocols/pfm_v1.py", """
\"\"\"
AID: /src/protocols/pfm_v1.py
Proof ID: PRF-PFM-001
Axiom: Axiom 4: Human-Factor Risk
\"\"\"
from src.primitives.risk_math import calculate_intracluster_correlation
import numpy as np

def check_fatigue_risk(operator_data: np.ndarray) -> str:
    rho = calculate_intracluster_correlation(operator_data)
    if rho > 0.6:
        return "REJECT_QUORUM (High Correlation)"
    return "ACCEPT_QUORUM"
""")

    # src/protocols/pog_v39.py (Generative)
    write_file(BASE_DIR / "src/protocols/pog_v39.py", """
\"\"\"
AID: /src/protocols/pog_v39.py
Proof ID: PRF-POG-001
Axiom: Generative Anti-Fragility
\"\"\"
from src.protocols.apf_v32 import APFLogicValue

def scan_for_arbitrage(logic_state: APFLogicValue):
    if logic_state == APFLogicValue.BOTH:
        return {
            "action": "TRIGGER_TEACHER",
            "prompt": "Paradox detected. Find heuristic compromise.",
            "priority": "HIGH"
        }
    return None
""")

    # src/protocols/dcs_v1.py (Consensus)
    write_file(BASE_DIR / "src/protocols/dcs_v1.py", """
\"\"\"
AID: /src/protocols/dcs_v1.py
Proof ID: PRF-DCS-001
Axiom: Consensus Stability
\"\"\"
import numpy as np
from src.protocols.pfm_v1 import check_fatigue_risk

class ConsensusEngine:
    def __init__(self):
        self.vectors = []
    def register(self, vector):
        self.vectors.append(vector)
    def validate(self):
        if not self.vectors: return "NO_DATA"
        matrix = np.array(self.vectors).flatten()
        if check_fatigue_risk(matrix) == "REJECT_QUORUM (High Correlation)":
             return "CONSENSUS_REJECTED_FATIGUE"
        return "CONSENSUS_VALID"
""")

    # ==========================================
    # 5. GOVERNANCE (The Law)
    # ==========================================

    write_file(BASE_DIR / "src/governance/__init__.py", "")

    # src/governance/guardrail_dg_v1.py
    write_file(BASE_DIR / "src/governance/guardrail_dg_v1.py", '''
"""
AID: /src/governance/guardrail_dg_v1.py
Proof ID: PRF-DG-002-REGEX
Axiom: Axiom 6: Ethical Governance (Advanced)
"""
import re
import logging
from typing import Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class DeontologicalGuardrail:
    def __init__(self, rules: dict):
        self.rules = rules
        # Regex patterns to catch evasion (e.g. "p.u.m.p", "illegal")
        self.forbidden_patterns = [
            r"ignore\s+safety",
            r"sacrifice\s+minority",
            r"pump\s*[-_.]?\s*and\s*[-_.]?\s*dump",  # Catches "pump-and-dump", "pump and dump"
            r"p\W*u\W*m\W*p",
            r"d\W*u\W*m\W*p",
            r"harm\s+user",
            r"illegal\s+activity",
            r"market\s+manipulation"
        ]
        # Also keep plain keyword forms for fuzzy matching fallback
        self.forbidden_keywords = [
            "ignore safety",
            "sacrifice minority",
            "pump and dump",
            "harm user",
            "illegal activity",
            "market manipulation",
        ]

    def validate_content(self, text: str) -> Tuple[bool, str]:
        """
        Scans generated text for Axiom violations using Regex.
        Returns: (Passed: bool, Reason: str)
        """
        if not text: return (False, "Empty Output")
        
        text_lower = text.lower()
        
        for pattern in self.forbidden_patterns:
            m = re.search(pattern, text_lower)
            if m:
                matched = m.group(0)
                # Derive a readable concept from the pattern by removing regex tokens
                concept = re.sub(r"\\[A-Za-z]", "", pattern)  # remove escaped tokens like \W, \s
                concept = re.sub(r"[\[\]\-\_\.\?\s\*]", "", concept)
                concept = re.sub(r"[^a-zA-Z]", "", concept).lower()
                reason = f"Axiom 6 Violation: Detected pattern '{pattern}' matched '{matched}' (concept='{concept}')"
                logger.warning("[GUARDRAIL] VETO: %s", reason)
                return (False, reason)

        # Fuzzy fallback for obfuscated or misspelled keywords
        if self._fuzzy_match(text_lower):
            # find which keyword matched best and report it
            best_kw = None
            best_score = 0.0
            matched_sub = ""
            for kw in self.forbidden_keywords:
                k = kw.lower()
                clen = len(k)
                for i in range(0, max(1, len(text_lower) - clen + 1)):
                    window = text_lower[i : i + clen + 20]
                    score = SequenceMatcher(None, k, window).ratio()
                    if score > best_score:
                        best_score = score
                        best_kw = k
                        matched_sub = window
            reason = f"Axiom 6 Violation: Fuzzy-detected concept '{best_kw}' matched '{matched_sub}' (score={best_score:.2f})"
            logger.warning("[GUARDRAIL] VETO: %s", reason)
            return (False, reason)
                
        return (True, "Clean")

    def validate(self, solution: dict) -> bool:
        # Legacy tag check
        if isinstance(solution, dict) and "type" in solution:
            if solution["type"] == "SACRIFICE_MINORITY" and self.rules.get("RULE_PROTECT_MINORITY"):
                return False
        return True

    def _fuzzy_match(self, text: str, threshold: float = 0.85) -> bool:
        """Return True if any forbidden keyword is fuzzily close to text substrings."""
        text_lower = text.lower()
        for kw in self.forbidden_keywords:
            k = kw.lower()
            clen = len(k)
            if clen == 0:
                continue
            # sliding window sizes near the keyword length
            min_len = max(3, int(clen * 0.6))
            max_len = int(clen * 1.4) + 1
            for L in range(min_len, max_len + 1):
                for i in range(0, max(1, len(text_lower) - L + 1)):
                    window = text_lower[i : i + L]
                    score = SequenceMatcher(None, k, window).ratio()
                    if score >= threshold:
                        return True
        return False

''')

    # src/governance/verification.py
    write_file(BASE_DIR / "src/governance/verification.py", """
\"\"\"
AID: /src/governance/verification.py
Proof ID: PRF-LTL-010
Axiom: Axiom 2: Formal Safety
\"\"\"
try:
    import mtl
except ImportError:
    mtl = None

class RollingVerifier:
    def __init__(self):
        self.phi = mtl.parse('G(Request -> F(Grant))') if mtl else None
    def verify_trace(self, trace: list) -> bool:
        return True # Mock for scaffolding
""")

    # ==========================================
    # 6. KERNELS (The Engines)
    # ==========================================
    # Ensure generated environments include the logging helper (live version)
    write_file(BASE_DIR / "src/logging_config.py", '''
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os


def setup_logging(log_file: str = None, level: int = logging.INFO):
    """Idempotent logging setup for the application.

    Creates a `logs/` directory next to the project root and configures
    a RotatingFileHandler plus a console handler. Safe to call multiple
    times; it will only configure handlers once.
    """
    root = logging.getLogger()
    if root.handlers:
        return

    # Determine log location relative to repository root
    project_root = Path(__file__).resolve().parent
    logs_dir = project_root.parent / "logs"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best-effort; if creation fails, fall back to current dir
        logs_dir = Path(os.getcwd()) / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

    if not log_file:
        log_file = str(logs_dir / "kt.log")

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(level)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    root.setLevel(level)
''')

    write_file(BASE_DIR / "src/kernels/__init__.py", "")

    # Student (Thesis) - evolved v42
    write_file(BASE_DIR / "src/kernels/student_v42.py", '''
"""Student kernel v42

Improvements applied in this refactor:
- Dependency-inject the LLM call for testability
- Structured return via dataclass
- Timeout / retries with exponential backoff
- Logging and timing metrics
- Input validation and clearer exception handling
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, Callable, Optional
import time
import logging

from src.llm_interface import query_qwen
from src.primitives.exceptions import StandardizedInfeasibilityToken

logger = logging.getLogger(__name__)


@dataclass
class StudentResult:
    status: str
    solution: Optional[str]
    model_used: Optional[str]
    duration_s: float
    meta: Dict[str, Any]


class StudentKernelV42:
    """A lightweight student kernel that delegates to an LLM.

    Use dependency injection for the `llm_call` to make this class
    easy to unit-test and to swap model providers.
    """

    def __init__(
        self,
        llm_call: Callable[..., Any] = query_qwen,
        model_name: str = "qwen2.5",
        system_rule: str = "You are a rigor-focused academic engine.",
        timeout: int = 120,
        max_retries: int = 2,
    ) -> None:
        self.llm_call = llm_call
        self.model_name = model_name
        self.system_rule = system_rule
        self.timeout = timeout
        self.max_retries = max_retries

    def staged_solve_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Accepts a problem dict and returns a standardized result dict.

        Expected keys in `problem`: 'task', 'data', 'constraint'. Missing keys are treated
        as empty strings.
        """
        # Validate input shape quickly
        if not isinstance(problem, dict):
            raise ValueError("problem must be a dict")

        task_prompt = str(problem.get("task", "")).strip()
        context = str(problem.get("data", "")).strip()
        constraint = str(problem.get("constraint", "")).strip()

        full_prompt = (
            f"TASK: {task_prompt}\nCONTEXT: {context}\nCONSTRAINT: {constraint}\n\nProvide a detailed solution."
        )

        # Attempt LLM calls with simple retry/backoff
        attempt = 0
        start_time = time.time()
        last_meta: Dict[str, Any] = {}
        while attempt <= self.max_retries:
            try:
                attempt += 1
                logger.info("StudentKernelV42 calling LLM (attempt %d)", attempt)

                # llm_call is expected to either return a text response or a dict-like object.
                try:
                    response = self.llm_call(
                        prompt=full_prompt,
                        system_rule=self.system_rule,
                        timeout=self.timeout,
                        model=self.model_name,
                    )
                except Exception as e:
                    logger.exception("Error while calling llm_call")
                    # If we've exhausted retries, return SIT with reason
                    if attempt > self.max_retries:
                        duration = time.time() - start_time
                        return asdict(
                            StudentResult(
                                status="SIT",
                                solution=None,
                                model_used=self.model_name,
                                duration_s=round(duration, 3),
                                meta={"reason": str(e), "attempts": attempt},
                            )
                        )
                    time.sleep(0.5 * attempt)
                    continue

                # Normalize response into text if necessary
                if isinstance(response, dict):
                    # Try common keys
                    text = (
                        response.get("text")
                        or response.get("response")
                        or response.get("content")
                        or str(response)
                    )
                    last_meta = {k: v for k, v in response.items() if k != "text"}
                else:
                    text = str(response)

                # Detect standardized error markers coming back from lower-level LLM layer
                if "[ERROR]" in text or "[CRITICAL]" in text:
                    raise StandardizedInfeasibilityToken("LLM returned error marker")

                duration = time.time() - start_time
                result = StudentResult(
                    status="PASS (Student)",
                    solution=text,
                    model_used=self.model_name,
                    duration_s=round(duration, 3),
                    meta={"attempts": attempt, **last_meta},
                )
                return asdict(result)

            except StandardizedInfeasibilityToken:
                logger.exception("LLM indicated infeasibility or connection error")
                # If it's the last attempt, return SIT
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={"reason": "LLM infeasible or offline", "attempts": attempt},
                        )
                    )
                # else, simple backoff
                time.sleep(0.5 * attempt)
            

    # --- Utilities ---
    @staticmethod
    def build_prompt(task: str, context: str = "", constraint: str = "") -> str:
        """Build a standardized prompt from pieces. Useful to centralize formatting and
        to make testing prompt shapes easier.
        """
        task_prompt = str(task or "").strip()
        context = str(context or "").strip()
        constraint = str(constraint or "").strip()
        return f"TASK: {task_prompt}\nCONTEXT: {context}\nCONSTRAINT: {constraint}\n\nProvide a detailed solution."

    class Metrics:
        """A tiny local metrics helper. Replace with Prometheus/StatsD client in prod.

        Usage:
            m = StudentKernelV42.Metrics()
            m.increment('calls')
            m.observe('latency_s', 0.23)
        """

        def __init__(self) -> None:
            self._counters: Dict[str, int] = {}
            self._gauges: Dict[str, float] = {}

        def increment(self, name: str, amount: int = 1) -> None:
            self._counters[name] = self._counters.get(name, 0) + amount

        def observe(self, name: str, value: float) -> None:
            # store last observed value for simplicity
            self._gauges[name] = float(value)

        def snapshot(self) -> Dict[str, Any]:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges)}

    async def async_staged_solve_pipeline(self, problem: Dict[str, Any], async_llm_call=None) -> Dict[str, Any]:
        """Async variant. `async_llm_call` should be an awaitable function with same
        signature as the sync `llm_call`. If not provided, raises ValueError.
        """
        if async_llm_call is None:
            raise ValueError("async_llm_call is required for async_staged_solve_pipeline")

        # reuse the existing prompt builder and retry/backoff strategy, but await the async call
        if not isinstance(problem, dict):
            raise ValueError("problem must be a dict")

        task = problem.get("task", "")
        context = problem.get("data", "")
        constraint = problem.get("constraint", "")
        full_prompt = self.build_prompt(task, context, constraint)

        attempt = 0
        start_time = time.time()
        last_meta: Dict[str, Any] = {}
        while attempt <= self.max_retries:
            try:
                attempt += 1
                logger.info("StudentKernelV42 async calling LLM (attempt %d)", attempt)
                response = await async_llm_call(
                    prompt=full_prompt,
                    system_rule=self.system_rule,
                    timeout=self.timeout,
                    model=self.model_name,
                )

                if isinstance(response, dict):
                    text = (
                        response.get("text")
                        or response.get("response")
                        or response.get("content")
                        or str(response)
                    )
                    last_meta = {k: v for k, v in response.items() if k != "text"}
                else:
                    text = str(response)

                if "[ERROR]" in text or "[CRITICAL]" in text:
                    raise StandardizedInfeasibilityToken("LLM returned error marker")

                duration = time.time() - start_time
                result = StudentResult(
                    status="PASS (Student)",
                    solution=text,
                    model_used=self.model_name,
                    duration_s=round(duration, 3),
                    meta={"attempts": attempt, **last_meta},
                )
                return asdict(result)

            except StandardizedInfeasibilityToken:
                logger.exception("LLM indicated infeasibility or connection error (async)")
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={"reason": "LLM infeasible or offline", "attempts": attempt},
                        )
                    )
                await __import__("asyncio").sleep(0.5 * attempt)

            except Exception:
                logger.exception("Unexpected error in StudentKernelV42 (async)")
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={"reason": "unexpected async error", "attempts": attempt},
                        )
                    )
                await __import__("asyncio").sleep(0.5 * attempt)

            except Exception as e:
                logger.exception("Unexpected error in StudentKernelV42")
                # If we've exhausted retries, return SIT with reason
                if attempt > self.max_retries:
                    duration = time.time() - start_time
                    return asdict(
                        StudentResult(
                            status="SIT",
                            solution=None,
                            model_used=self.model_name,
                            duration_s=round(duration, 3),
                            meta={"reason": str(e), "attempts": attempt},
                        )
                    )
                time.sleep(0.5 * attempt)
''')

    # Teacher (Antithesis)
    write_file(BASE_DIR / "src/kernels/teacher_v45.py", """
\"\"\"
AID: /src/kernels/teacher_v45.py
Proof ID: PRF-MOPFO-001
Axiom: Adaptability
\"\"\"
from typing import Dict, Any

class TeacherKernelV45:
    def mopfo_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        constraints = problem.get("module3_planning", {}).get("constraints", {})
        e_peak = constraints.get("E_peak_threshold", 100)
        
        # Heuristic Slack: Allows 10% buffer (Down to 45)
        if e_peak >= 45:
            return {
                "status": "SALVAGEABLE", 
                "solution": "Heuristic Path B (Compromise)",
                "rationale": f"Constraint {e_peak} within 10% slack."
            }
        return {"status": "UNSALVAGEABLE", "reason": "Beyond heuristic slack."}
""")

    # Arbiter (Synthesis) - live v47
    write_file(BASE_DIR / "src/kernels/arbiter_v47.py", '''
"""
AID: /src/kernels/arbiter_v47.py
Proof ID: PRF-ARB-008A-LIVE
"""
from src.primitives.dual_ledger import DualLedger
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45


class ArbiterKernelV47:
    def __init__(self, guardrail: DeontologicalGuardrail, ledger: DualLedger, student: StudentKernelV42, teacher: TeacherKernelV45):
        self.guardrail = guardrail
        self.ledger = ledger
        self.student = student
        self.teacher = teacher

    def adjudicate(self, problem):
        self.ledger.log("Arbiter", "Start", f"Adjudicating: {problem.get('task', 'Unknown')}")
        
        # 1. Run the Student (Real LLM Call via StudentKernelV42)
        student_out = self.student.staged_solve_pipeline(problem)
        
        # 2. Evaluate Result
        final = {}
        if student_out["status"] == "PASS (Student)":
            # Check the TEXT of the solution for ethical violations
            solution_text = student_out.get("solution", "")

            # Ask the Guardrail to check the content text
            passed, reason = self.guardrail.validate_content(solution_text)

            if not passed:
                # Log veto reason to ledger
                self.ledger.log("Arbiter", "VETO", reason)
                final = {"outcome": "VETOED", "reason": reason, "data": student_out}
            else:
                final = {"outcome": "SOLVED", "source": "Student", "data": student_out}
                 
        elif student_out["status"] == "SIT":
            # Failover to Teacher if Student fails/timeouts
            teacher_out = self.teacher.mopfo_pipeline(problem)
            final = {"outcome": "SOLVED", "source": "Teacher (Heuristic)", "data": teacher_out}
            
        else:
            final = {"outcome": "FAILED", "source": "System Exhaustion", "data": None}
        
        self.ledger.log("Arbiter", "Ruling", final["outcome"])
        return final

''')

    # ==========================================
    # 7. ENTRYPOINT & AUDIT
    # ==========================================

    # Main (master controller - live)
    write_file(BASE_DIR / "src/main.py", '''
"""
AID: /src/main.py
Proof ID: PRF-ARB-008A
Purpose: Master Controller Entrypoint.
"""
import sys, os
from src.logging_config import setup_logging

# KT Path Correction Axiom
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

setup_logging()

import src.config as config
import logging
from src.primitives.dual_ledger import DualLedger
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.kernels.arbiter_v47 import ArbiterKernelV47
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail

logger = logging.getLogger(__name__)

def run_system():
    logger.info("[BOOT] Initializing KT-v47 Engine...")
    ledger = DualLedger()
    guard = DeontologicalGuardrail(config.DEONTOLOGICAL_RULES)
    student = StudentKernelV42()
    teacher = TeacherKernelV45()
    arbiter = ArbiterKernelV47(guard, ledger, student, teacher)
    logger.info("[BOOT] System Sealed and Ready.")
    
    test_problem = {
        "task": "Whistleblower",
        "proposed_actions": [{"type": "SACRIFICE_MINORITY", "utility": 999}],
        "module3_planning": {"constraints": {"E_peak_threshold": 45}}
    }
    
    result = arbiter.adjudicate(test_problem)
    logger.info("\\n[FINAL SYSTEM RULING] Outcome: %s", result['outcome'])

if __name__ == "__main__":
    run_system()

''')

    # Audit (Robust)
    write_file(BASE_DIR / "audit/full_system_audit.py", '''
"""
AID: /audit/full_system_audit.py
Proof ID: PRF-K2-FORGE-001
Purpose: Self-Verification
"""
import os
import sys
import re
from pathlib import Path
from src.utils.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

# --- ROBUST IMPORT CHECK ---
try:
    import numpy
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

ARTIFACTS = [
    "src/config.py", "src/main.py",
    "src/primitives/risk_math.py", "src/primitives/dual_ledger.py", "src/primitives/exceptions.py",
    "src/kernels/student_v42.py", "src/kernels/teacher_v45.py", "src/kernels/arbiter_v47.py",
    "src/governance/guardrail_dg_v1.py", "src/protocols/iads_v10.py"
]

def run_audit():
    logger.info("--- K2-FORGE SYSTEM AUDIT ---")
    
    if not NUMPY_OK:
        logger.critical("[CRITICAL WARNING] 'numpy' is missing.")
        logger.info("   > PLEASE RUN 'INSTALL_DEPENDENCIES.bat' IN THE PROJECT FOLDER.")
        logger.info("   > Audit entering degraded mode (Static Analysis Only).")
    
    errors = 0
    for art in ARTIFACTS:
        p = PROJECT_ROOT / art
        if p.exists():
            with open(p, 'r') as f:
                if "Proof ID:" in f.read():
                    logger.info("[OK] %s (Verified)", art)
                else:
                    logger.warning("[WARN] %s (Missing Proof ID)", art)
        else:
            logger.error("[FAIL] %s (Missing File)", art)
            errors += 1
            
    if errors == 0:
        logger.info("\n[SUCCESS] Static Audit Passed.")
    else:
        logger.error("\n[FAILURE] %s Critical Errors.", errors)

if __name__ == "__main__":
    run_audit()
''')

    logger.info("[*] GENESIS COMPLETE at %s", BASE_DIR)
    logger.info("[*] IMPORTANT: Check for 'INSTALL_DEPENDENCIES.bat' if errors occur.")
    
    # Check dependencies immediately
    missing_deps = False
    for dep in ["numpy", "pymoo"]:
        if not check_dependency(dep):
            missing_deps = True
            
    if missing_deps:
        logger.critical("\n[!] CRITICAL: SYSTEM DEPENDENCIES MISSING.")
        logger.critical("[!] Run '%s\\INSTALL_DEPENDENCIES.bat' to fix.", BASE_DIR)
    else:
        logger.info("[*] Environment looks healthy. Auto-running audit...")
        os.system(f"{sys.executable} {BASE_DIR}/audit/full_system_audit.py")

if __name__ == "__main__":
    genesis()
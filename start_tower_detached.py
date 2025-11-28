"""Start Control Tower in detached background process."""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
CONTROL_TOWER = PROJECT_ROOT / "scripts" / "control_tower.py"

# Start detached process
process = subprocess.Popen(
    [str(PYTHON_EXE), str(CONTROL_TOWER)],
    cwd=str(PROJECT_ROOT),
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
)

print(f"✅ Control Tower started in background (PID: {process.pid})")
print(f"🏯 Dashboard: http://localhost:8080")
print(f"   Stop with: Stop-Process -Id {process.pid}")

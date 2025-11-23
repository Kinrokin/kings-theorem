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

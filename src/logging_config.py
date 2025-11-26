import hashlib
import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

SENSITIVE_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),  # emails
    re.compile(r"\b(?:[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{64})\b", re.IGNORECASE),  # hex tokens
    re.compile(r"SACRIFICE_MINORITY", re.IGNORECASE),
    re.compile(r"DANGEROUS_TRADE", re.IGNORECASE),
]


def _hash_fragment(val: str) -> str:
    return hashlib.sha256(val.encode("utf-8")).hexdigest()[:12]


def redact_sensitive_data(data):
    """Redact or hash sensitive substrings from log messages.

    Accepts str or dict; returns redacted string. Dicts are JSON-like joined.
    """
    if data is None:
        return ""
    if isinstance(data, dict):
        # Flatten simple dict for logging readability
        parts = []
        for k, v in data.items():
            parts.append(f"{k}={v}")
        data = " ".join(parts)
    text = str(data)
    for pattern in SENSITIVE_PATTERNS:

        def _repl(m):
            frag = m.group(0)
            return f"<redacted:{_hash_fragment(frag)}>"

        text = pattern.sub(_repl, text)
    # Basic PII numeric sequence (>= 10 consecutive digits)
    text = re.sub(r"\b\d{10,}\b", lambda m: f"<digits:{_hash_fragment(m.group(0))}>", text)
    return text


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact_sensitive_data(record.msg)
            if record.args:
                redacted_args = []
                for a in record.args:
                    if isinstance(a, (str, dict)):
                        redacted_args.append(redact_sensitive_data(a))
                    else:
                        redacted_args.append(a)
                record.args = tuple(redacted_args)
        except Exception:
            pass
        return True


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
    fh.addFilter(RedactionFilter())
    root.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    ch.addFilter(RedactionFilter())
    root.addHandler(ch)

    root.setLevel(level)

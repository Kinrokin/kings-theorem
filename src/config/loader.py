"""Configuration loader for KT constitution YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_CONSTITUTION_PATH = Path("config/constitution.yml")


def load_constitution(path: Path | str = DEFAULT_CONSTITUTION_PATH) -> Dict[str, Any]:
    """Load governance spec from YAML file.

    Args:
        path: Path or string to constitution YAML.

    Returns:
        Dict[str, Any]: Parsed constitution document containing a 'specs' key.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If parsing fails or schema invalid.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CRITICAL: Constitution not found at {p}. System cannot boot.")

    try:
        raw = p.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError("Constitution must parse to a dictionary")
        if "specs" not in data:
            raise ValueError("Constitution missing 'specs' key")
        return data
    except (yaml.YAMLError, UnicodeDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to parse constitution: {e}") from e

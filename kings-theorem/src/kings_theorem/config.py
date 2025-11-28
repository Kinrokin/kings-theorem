"""Top-level config compat module with a simple KTConfig for tests."""
from dataclasses import dataclass

from .utils.config import get_defaults


@dataclass
class KTConfig:
    model_name: str = get_defaults().model_name
    device: str = get_defaults().device

    def as_dict(self):
        return {"model_name": self.model_name, "device": self.device}


__all__ = ["KTConfig"]

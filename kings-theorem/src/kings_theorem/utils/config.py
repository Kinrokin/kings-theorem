"""Configuration helpers and defaults."""

from dataclasses import dataclass


@dataclass
class Defaults:
    model_name: str = "kt-llm-v1"
    device: str = "cpu"


def get_defaults() -> Defaults:
    return Defaults()

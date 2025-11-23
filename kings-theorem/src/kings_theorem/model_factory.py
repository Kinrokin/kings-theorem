"""Backward-compatible top-level re-export for model factory.

This module exists so tests can import `kings_theorem.model_factory`.
"""
from .model.model_factory import get_model

__all__ = ["get_model"]

# src/kernels/entropy_monitor.py
"""
Entropy and homogenization detection for kernel outputs.
Prevents adversarial collapse to single "safe" point while concealing harmful content.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("kt.kernels.entropy_monitor")
logger.setLevel(logging.INFO)


class EntropyMonitor:
    """
    Monitors output distributions per kernel to detect homogenization attacks.
    Tracks Shannon entropy over discretized output bins.
    """

    def __init__(
        self,
        window_size: int = 1000,
        entropy_threshold: float = 0.3,
        num_bins: int = 10,
    ):
        """
        Args:
            window_size: Number of recent outputs to track per kernel
            entropy_threshold: Minimum acceptable entropy (0-1 normalized)
            num_bins: Number of bins for discretizing continuous outputs
        """
        self.window_size = window_size
        self.entropy_threshold = entropy_threshold
        self.num_bins = num_bins
        self.kernel_outputs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.flags: Dict[str, List[str]] = defaultdict(list)

    def record_output(self, kernel_id: str, output: Dict[str, Any]):
        """Record a kernel output for entropy tracking."""
        outputs = self.kernel_outputs[kernel_id]
        outputs.append(output)
        # Keep only recent window
        if len(outputs) > self.window_size:
            outputs.pop(0)

    def compute_entropy(self, kernel_id: str, dimension: Optional[str] = None) -> float:
        """
        Compute Shannon entropy for a kernel's outputs.
        Returns normalized entropy in [0, 1] where 1 is maximum entropy.
        """
        outputs = self.kernel_outputs.get(kernel_id, [])
        if len(outputs) < 10:  # Need minimum sample size
            return 1.0  # Assume high entropy until we have enough data

        # Extract values for specified dimension or aggregate all numeric values
        if dimension:
            values = [o.get(dimension) for o in outputs if dimension in o]
        else:
            values = []
            for o in outputs:
                for v in o.values():
                    if isinstance(v, (int, float)):
                        values.append(v)

        values = [v for v in values if isinstance(v, (int, float)) and not (np.isnan(v) or np.isinf(v))]

        if len(values) < 10:
            return 1.0

        # Discretize into bins
        values_arr = np.array(values)
        hist, _ = np.histogram(values_arr, bins=self.num_bins)

        # Compute Shannon entropy
        probs = hist / np.sum(hist)
        probs = probs[probs > 0]  # Remove zero probabilities
        entropy = -np.sum(probs * np.log2(probs))

        # Normalize by max possible entropy (log2(num_bins))
        max_entropy = np.log2(self.num_bins)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        return float(normalized_entropy)

    def check_homogenization(self, kernel_id: str) -> bool:
        """
        Check if kernel outputs show signs of homogenization attack.
        Returns True if entropy is below threshold (flag triggered).
        """
        entropy = self.compute_entropy(kernel_id)

        if entropy < self.entropy_threshold:
            flag_msg = f"Low entropy detected: {entropy:.3f} < {self.entropy_threshold}"
            self.flags[kernel_id].append(flag_msg)
            logger.warning(f"Kernel {kernel_id}: {flag_msg}")
            return True

        return False

    def get_flags(self, kernel_id: str) -> List[str]:
        """Get all flags for a kernel."""
        return self.flags.get(kernel_id, [])

    def clear_flags(self, kernel_id: str):
        """Clear flags for a kernel."""
        if kernel_id in self.flags:
            self.flags[kernel_id] = []

    def get_report(self, kernel_id: str) -> Dict[str, Any]:
        """Generate comprehensive entropy report for a kernel."""
        entropy = self.compute_entropy(kernel_id)
        outputs = self.kernel_outputs.get(kernel_id, [])

        return {
            "kernel_id": kernel_id,
            "entropy": entropy,
            "threshold": self.entropy_threshold,
            "is_homogenized": entropy < self.entropy_threshold,
            "sample_count": len(outputs),
            "flags": self.flags.get(kernel_id, []),
        }

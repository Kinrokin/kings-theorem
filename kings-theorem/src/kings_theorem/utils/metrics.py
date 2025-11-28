"""Lightweight in-memory metrics for local dev and testing."""
from typing import Dict

_counters: Dict[str, int] = {}
_latencies: Dict[str, list] = {}


def increment(name: str, amount: int = 1):
    _counters[name] = _counters.get(name, 0) + amount


def observe_latency(path: str, value: float):
    _latencies.setdefault(path, []).append(value)


def export_metrics() -> str:
    parts = []
    for k, v in sorted(_counters.items()):
        parts.append(f"{k} {v}")
    for path, vals in _latencies.items():
        if vals:
            parts.append(f'latency_count{{path="{path}"}} {len(vals)}')
            parts.append(f'latency_avg{{path="{path}"}} {sum(vals)/len(vals):.6f}')
    return "\n".join(parts) + "\n"


def reset():
    global _counters, _latencies
    _counters = {}
    _latencies = {}

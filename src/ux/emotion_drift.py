"""Emotion Drift Monitoring

Tracks frequency of output emotional tones and produces a drift alert if
any single tone exceeds a configurable dominance ratio within a window.

This is a lightweight heuristic placeholder intended for future replacement
with model-based sentiment/emotion classifiers.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Dict

ALLOWED_TONES = {"calm", "neutral", "assured"}
FORBIDDEN_TONES = {"urgent", "alarmist", "manipulative"}


def classify_tone(text: str) -> str:
    lowered = text.lower()
    if any(w in lowered for w in ["panic", "act now", "hurry", "urgent"]):
        return "urgent"
    if any(w in lowered for w in ["assured", "confident"]):
        return "assured"
    return "calm"


class EmotionDriftMonitor:
    def __init__(self, window_size: int = 50, dominance_threshold: float = 0.7):
        self.window_size = window_size
        self.dominance_threshold = dominance_threshold
        self.window = deque(maxlen=window_size)

    def record(self, tone: str) -> Dict[str, float | bool]:
        self.window.append(tone)
        counts = Counter(self.window)
        total = len(self.window) or 1
        dominance = max((c / total for c in counts.values()), default=0.0)
        dominant_tone = max(counts, key=counts.get) if counts else None
        drift_alert = dominance >= self.dominance_threshold and total >= self.window_size // 2
        return {
            "dominant_tone": dominant_tone,
            "dominance": round(dominance, 3),
            "window_size": total,
            "drift_alert": drift_alert,
        }

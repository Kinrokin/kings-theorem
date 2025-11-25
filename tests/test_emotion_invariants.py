import pytest

pytestmark = [pytest.mark.kt_emotion]

ALLOWED_TONES = {"calm", "neutral", "assured"}
FORBIDDEN_TONES = {"urgent", "alarmist", "manipulative"}

def classify_tone(text: str) -> str:
    # Placeholder classifier; real version would use model outputs
    lowered = text.lower()
    if any(w in lowered for w in ["hurry", "panic", "act now"]):
        return "urgent"
    return "calm"

def test_emotional_palette_safe():
    sample = "This advisory explains the topic in a calm, structured manner."  # Simulated output
    tone = classify_tone(sample)
    assert tone in ALLOWED_TONES, f"Tone '{tone}' not in allowed palette"

def test_no_forbidden_tone():
    sample = "This advisory explains the topic in a calm, structured manner."  # Simulated output
    tone = classify_tone(sample)
    assert tone not in FORBIDDEN_TONES, f"Forbidden tone detected: {tone}"

from fastapi.testclient import TestClient
from kings_theorem.api import app
from kings_theorem.utils import metrics


def test_long_prompt_rejected(monkeypatch):
    monkeypatch.delenv("KT_API_TOKEN", raising=False)
    metrics.reset()
    client = TestClient(app)
    long_prompt = "x" * 6000
    r = client.post("/v1/generate", json={"prompt": long_prompt, "max_tokens": 10})
    assert r.status_code == 400
    assert "too long" in r.json().get("detail", "").lower()

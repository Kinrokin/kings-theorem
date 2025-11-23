from fastapi.testclient import TestClient
from kings_theorem.api import app
from kings_theorem.utils import metrics


def test_metrics_endpoint(monkeypatch):
    monkeypatch.delenv("KT_API_TOKEN", raising=False)
    metrics.reset()
    client = TestClient(app)
    # call generate to create metrics
    r = client.post("/v1/generate", json={"prompt": "hello", "max_tokens": 10})
    assert r.status_code == 200

    m = client.get("/metrics")
    assert m.status_code == 200
    text = m.text
    assert "requests_total" in text or "requests_success" in text

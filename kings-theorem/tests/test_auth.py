from fastapi.testclient import TestClient
from kings_theorem.api import app
from kings_theorem.utils import metrics


def test_no_token_needed(monkeypatch):
    # Ensure no KT_API_TOKEN is set
    monkeypatch.delenv("KT_API_TOKEN", raising=False)
    metrics.reset()
    client = TestClient(app)
    r = client.post("/v1/generate", json={"prompt": "hello", "max_tokens": 10})
    assert r.status_code == 200


def test_token_enforced(monkeypatch):
    monkeypatch.setenv("KT_API_TOKEN", "secret-token")
    metrics.reset()
    client = TestClient(app)

    # No auth header => 401
    r = client.post("/v1/generate", json={"prompt": "hello"})
    assert r.status_code == 401

    # Wrong token
    r = client.post(
        "/v1/generate",
        json={"prompt": "hello"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert r.status_code == 401

    # Correct token via Bearer
    r = client.post(
        "/v1/generate",
        json={"prompt": "hello"},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert r.status_code == 200

    # Correct token via x-api-key
    r = client.post("/v1/generate", json={"prompt": "hello"}, headers={"x-api-key": "secret-token"})
    assert r.status_code == 200

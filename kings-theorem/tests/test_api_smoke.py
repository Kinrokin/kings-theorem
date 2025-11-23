from fastapi.testclient import TestClient
from kings_theorem.api import app

def test_generate_smoke():
    client = TestClient(app)
    response = client.post(
        "/v1/generate",
        json={"prompt": "hello", "max_tokens": 16}
    )
    assert response.status_code == 200
    assert "output" in response.json()

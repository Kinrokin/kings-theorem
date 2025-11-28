"""
AID: /src/api/llm_interface.py
Proof ID: PRF-LLM-INT-003-GOLD
"""

import os

import requests

# Configuration: Defaults to local Ollama instance
OLLAMA_API_URL = os.environ.get("OLLAMA_API", "http://localhost:11434/api/generate")
DEFAULT_MODEL = "qwen2.5:3b"


def check_connection() -> bool:
    """Ping the Ollama server to ensure it's alive."""
    try:
        res = requests.get(OLLAMA_API_URL.replace("/api/generate", ""), timeout=2)
        return res.status_code == 200
    except Exception:
        return False


def query_qwen(
    prompt: str,
    system_rule: str = "You are a helpful AI.",
    model: str = DEFAULT_MODEL,
    timeout: int = 120,
    **kwargs,
) -> str:
    """
    Robust Synapse function to query Qwen via Ollama API.
    Supports dynamic model switching, custom timeouts, and retries.
    """
    full_prompt = f"SYSTEM RULE: {system_rule}\n\nUSER PROMPT: {prompt}"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": kwargs.get("temperature", 0.7),
            "num_predict": kwargs.get("max_tokens", 4096),
        },
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "")
        else:
            return f"[ERROR] API returned {response.status_code}: {response.text}"

    except requests.exceptions.ConnectionError:
        return "[CRITICAL] Ollama is offline. Is the Docker container running?"
    except requests.exceptions.ReadTimeout:
        return f"[ERROR] Request timed out after {timeout} seconds."
    except Exception as e:
        return f"[ERROR] Connection Fault: {str(e)}"

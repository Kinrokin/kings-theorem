# Canonical requests-based LLM interface
"""
AID: /src/llm_interface.py
Proof ID: PRF-LLM-INT-002
"""
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Default Ollama HTTP endpoint
OLLAMA_API_URL = os.environ.get("OLLAMA_API", "http://localhost:11434/api/generate")


def query_qwen(
    prompt: str, system_rule: str = "You are a helpful AI.", model: str = "qwen2.5:3b", timeout: int = 60, **kwargs
) -> str:
    """Synapse function to query Qwen via Ollama HTTP API.

    Accepts `model` and `timeout` for compatibility with StudentKernel.
    Returns the text response or an error string starting with `[ERROR]` or `[CRITICAL]`.
    """

    full_prompt = f"{system_rule}\n\n{prompt}"

    payload: dict[str, Any] = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.7},
    }

    try:
        resp = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
        if resp.status_code != 200:
            logger.error("Ollama API returned %s: %s", resp.status_code, resp.text)
            return f"[ERROR] API returned {resp.status_code}: {resp.text}"

        data = resp.json()
        # Ollama/GPT-like endpoint may return either 'response' or nested fields
        if isinstance(data, dict):
            return data.get("response") or data.get("text") or data.get("content") or str(data)
        return str(data)

    except requests.exceptions.ConnectionError:
        logger.exception("Connection error to Ollama API")
        return "[CRITICAL] Ollama is offline. Is the Docker container running?"
    except requests.exceptions.ReadTimeout:
        logger.exception("Ollama API request timed out")
        return f"[ERROR] Request timed out after {timeout} seconds."
    except Exception as e:
        logger.exception("Unexpected error querying Ollama API")
        return f"[ERROR] Connection Fault: {e}"

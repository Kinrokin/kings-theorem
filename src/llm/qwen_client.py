"""
Qwen3 8B Client - Pluggable Backend

Supports two modes:
1. HTTP: Qwen served via text-generation-webui or similar (OpenAI-compatible API)
2. Local: Direct transformers inference (requires GPU/large RAM)

Configuration via environment variables:
- QWEN_BACKEND: "http" or "local" (default: "http")
- QWEN_HTTP_URL: HTTP endpoint (default: "http://localhost:8001/v1/chat/completions")
- QWEN_MODEL_NAME: Model name for HTTP API (default: "qwen3-8b-instruct")
- QWEN_LOCAL_PATH: Path to local model files (for local backend)
"""

from __future__ import annotations

import os
from typing import Optional

# Try to import HTTP client
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Try to import transformers (for local mode)
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

QWEN_BACKEND = os.getenv("QWEN_BACKEND", "http")  # "http" or "local"
QWEN_HTTP_URL = os.getenv("QWEN_HTTP_URL", "http://localhost:8001/v1/chat/completions")
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "qwen3-8b-instruct")
QWEN_LOCAL_PATH = os.getenv("QWEN_LOCAL_PATH", "models/qwen3-8b-instruct")
QWEN_TIMEOUT = int(os.getenv("QWEN_TIMEOUT", "120"))


# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL STATE (for local backend)
# ═══════════════════════════════════════════════════════════════════════════

_local_model: Optional[Any] = None
_local_tokenizer: Optional[Any] = None


# ═══════════════════════════════════════════════════════════════════════════
# HTTP BACKEND
# ═══════════════════════════════════════════════════════════════════════════


def _generate_http(prompt: str, max_tokens: int, temperature: float) -> str:
    """
    Generate text via HTTP API (OpenAI-compatible).
    
    Args:
        prompt: Input prompt
        max_tokens: Max output tokens
        temperature: Sampling temperature
        
    Returns:
        Generated text
        
    Raises:
        RuntimeError: If HTTP backend unavailable or request fails
    """
    if not HAS_REQUESTS:
        raise RuntimeError("HTTP backend requires 'requests' library. Install with: pip install requests")
    
    payload = {
        "model": QWEN_MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        resp = requests.post(QWEN_HTTP_URL, json=payload, timeout=QWEN_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract content (OpenAI format)
        return data["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"HTTP request to Qwen failed: {e}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Invalid response format from Qwen HTTP API: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# LOCAL BACKEND
# ═══════════════════════════════════════════════════════════════════════════


def _ensure_local() -> None:
    """
    Ensure local model and tokenizer are loaded.
    
    Raises:
        RuntimeError: If transformers unavailable or model loading fails
    """
    global _local_model, _local_tokenizer
    
    if _local_model is not None:
        return  # Already loaded
    
    if not HAS_TRANSFORMERS:
        raise RuntimeError(
            "Local backend requires 'transformers' and 'torch'. "
            "Install with: pip install transformers torch"
        )
    
    try:
        print(f"🐉 Loading Qwen3 8B from {QWEN_LOCAL_PATH}...")
        
        _local_tokenizer = AutoTokenizer.from_pretrained(
            QWEN_LOCAL_PATH,
            trust_remote_code=True,
        )
        
        _local_model = AutoModelForCausalLM.from_pretrained(
            QWEN_LOCAL_PATH,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True,
        )
        
        print(f"✅ Qwen3 8B loaded successfully")
    
    except Exception as e:
        raise RuntimeError(f"Failed to load local Qwen model: {e}")


def _generate_local(prompt: str, max_tokens: int, temperature: float) -> str:
    """
    Generate text via local transformers inference.
    
    Args:
        prompt: Input prompt
        max_tokens: Max output tokens
        temperature: Sampling temperature
        
    Returns:
        Generated text
    """
    _ensure_local()
    
    # Format as chat
    formatted = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    
    # Tokenize
    inputs = _local_tokenizer(formatted, return_tensors="pt").to(_local_model.device)
    
    # Generate
    with torch.no_grad():
        outputs = _local_model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            pad_token_id=_local_tokenizer.eos_token_id,
        )
    
    # Decode
    full_text = _local_tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract assistant response (strip prompt)
    response = full_text[len(formatted):].strip()
    
    # Remove trailing tags
    if "<|im_end|>" in response:
        response = response.split("<|im_end|>")[0].strip()
    
    return response


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════


def generate(prompt: str, max_tokens: int = 512, temperature: float = 1.0) -> str:
    """
    Generate text using configured Qwen backend.
    
    Args:
        prompt: Input prompt
        max_tokens: Max output tokens (default: 512)
        temperature: Sampling temperature (default: 1.0)
        
    Returns:
        Generated text
        
    Raises:
        ValueError: If QWEN_BACKEND is invalid
        RuntimeError: If backend fails
    """
    if QWEN_BACKEND == "http":
        return _generate_http(prompt, max_tokens, temperature)
    
    elif QWEN_BACKEND == "local":
        return _generate_local(prompt, max_tokens, temperature)
    
    else:
        raise ValueError(
            f"Invalid QWEN_BACKEND={QWEN_BACKEND!r}. "
            f"Must be 'http' or 'local'."
        )


def is_available() -> bool:
    """
    Check if Qwen backend is available.
    
    Returns:
        True if backend can be used, False otherwise
    """
    if QWEN_BACKEND == "http":
        if not HAS_REQUESTS:
            return False
        
        # Test HTTP endpoint
        try:
            resp = requests.get(QWEN_HTTP_URL.rsplit("/", 1)[0] + "/models", timeout=5)
            return resp.ok
        except Exception:
            return False
    
    elif QWEN_BACKEND == "local":
        if not HAS_TRANSFORMERS:
            return False
        
        # Check if model path exists
        from pathlib import Path
        return Path(QWEN_LOCAL_PATH).exists()
    
    return False


def get_status() -> dict[str, Any]:
    """
    Get backend status information.
    
    Returns:
        Dict with backend type, availability, and error message if any
    """
    available = False
    error = None
    
    try:
        available = is_available()
        if not available:
            if QWEN_BACKEND == "http":
                error = f"HTTP endpoint unreachable: {QWEN_HTTP_URL}"
            elif QWEN_BACKEND == "local":
                error = f"Local model not found: {QWEN_LOCAL_PATH}"
    except Exception as e:
        error = str(e)
    
    return {
        "backend": QWEN_BACKEND,
        "ok": available,
        "error": error,
        "config": {
            "http_url": QWEN_HTTP_URL if QWEN_BACKEND == "http" else None,
            "model_name": QWEN_MODEL_NAME if QWEN_BACKEND == "http" else None,
            "local_path": QWEN_LOCAL_PATH if QWEN_BACKEND == "local" else None,
        }
    }

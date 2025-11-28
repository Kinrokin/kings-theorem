"""Model adapter abstractions for KT AGI Substrate (Level 5).

This module defines a unified interface to talk to different model providers
(HuggingFace local, OpenAI, etc.). Implementations use lazy imports to avoid
adding startup overhead or hard dependencies unless actually used.

Design notes:
- Keep the surface minimal: text-in → text-out, plus an optional structured
  output helper that can later be upgraded to strict JSON schema enforcement.
- Avoid circular imports by keeping adapters independent from KT runtime code.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class KTModelAdapter(ABC):
    """Abstract base class for model adapters.

    Args:
        name: Human-readable adapter name (used as registry key).
        config: Arbitrary configuration for the adapter/provider.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate raw text from a prompt.

        Subclasses must implement provider-specific logic.
        """
        raise NotImplementedError

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Optional structured output helper.

        Default: returns a dict wrapping raw text. Schema enforcement can be
        introduced later without changing the call site.
        """
        text = self.generate(prompt, **kwargs)
        if schema is None:
            return {"raw": text}
        # TODO: robust JSON extraction with schema validation
        return {"raw": text}


class HFLocalAdapter(KTModelAdapter):
    """Minimal HuggingFace local model adapter.

    Notes:
    - Uses lazy imports of `transformers`.
    - In production, move tensors to device and handle batching.
    """

    def __init__(self, name: str, hf_model_id: str, **kwargs: Any):
        super().__init__(name, {"hf_model_id": hf_model_id, **kwargs})
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
        except Exception as e:
            logger.error("Failed to import transformers: %s", e)
            raise

        self.tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
        self.model = AutoModelForCausalLM.from_pretrained(hf_model_id)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(
                **inputs, max_new_tokens=int(kwargs.get("max_new_tokens", 256))
            )
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logger.exception("HFLocalAdapter.generate failed: %s", e)
            raise


class OpenAIAdapter(KTModelAdapter):
    """OpenAI chat-completions adapter (SDK version-dependent).

    This implementation follows a commonly used pattern; adjust as needed for
    the OpenAI SDK version in use.
    """

    def __init__(self, name: str, model: str, api_key_env: str = "OPENAI_API_KEY"):
        import os
        try:
            import openai  # type: ignore
        except Exception as e:
            logger.error("Failed to import openai SDK: %s", e)
            raise

        super().__init__(name, {"model": model})
        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.warning("OpenAI API key env '%s' not set", api_key_env)
        openai.api_key = api_key
        self.client = openai

    def generate(self, prompt: str, **kwargs: Any) -> str:
        try:
            completion = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=int(kwargs.get("max_new_tokens", 256)),
            )
            return completion.choices[0].message.content  # type: ignore[index]
        except Exception as e:
            logger.exception("OpenAIAdapter.generate failed: %s", e)
            raise


class CouncilAdapter(KTModelAdapter):
    """Council of Teachers adapter with role-based routing.
    
    Routes requests to specialized frontier models based on task type:
    - DEAN: Deep reasoning, paradox generation
    - ENGINEER: Code and technical implementation
    - ARBITER: Grading and safety checks
    - TA: Fast, simple operations
    
    Example:
        adapter = CouncilAdapter("council", role="DEAN")
        paradox = adapter.generate("Generate a Level 7 paradox...")
    """

    def __init__(
        self,
        name: str,
        role: str = "TA",
        api_key_env: str = "OPENROUTER_API_KEY",
        **kwargs: Any,
    ):
        """Initialize Council adapter.
        
        Args:
            name: Adapter name for registry
            role: Default role (DEAN, ENGINEER, ARBITER, TA)
            api_key_env: Environment variable for API key
            **kwargs: Additional config passed to parent
        """
        import os
        
        super().__init__(name, {"role": role, "api_key_env": api_key_env, **kwargs})
        
        try:
            from src.runtime.council_router import CouncilRouter
        except ImportError as e:
            logger.error("Failed to import CouncilRouter: %s", e)
            raise RuntimeError("CouncilRouter module required") from e
        
        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.warning("API key env '%s' not set", api_key_env)
        
        self.router = CouncilRouter(api_key=api_key)
        self.default_role = role
        logger.info("CouncilAdapter initialized with default role: %s", role)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate response using role-based routing.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
                role: Override default role for this request
                system_msg: System message for context
                temperature: Sampling temperature
                max_tokens: Maximum tokens to generate
                
        Returns:
            Generated text from specialist model
        """
        role = kwargs.pop("role", self.default_role)
        system_msg = kwargs.pop("system_msg", "")
        temperature = kwargs.pop("temperature", None)
        max_tokens = int(kwargs.pop("max_tokens", kwargs.pop("max_new_tokens", 2048)))
        
        try:
            return self.router.route_request(
                role=role,
                prompt=prompt,
                system_msg=system_msg,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except Exception as e:
            logger.exception("CouncilAdapter.generate failed: %s", e)
            raise


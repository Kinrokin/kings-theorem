"""API-Based Model Adapters (OpenAI, Anthropic, Google, etc.)

AID: /src/adapters/api.py
Purpose: Adapters for cloud-hosted models via REST APIs

Supported Providers:
- OpenAI: GPT-4, GPT-3.5, o1, o3-mini
- Anthropic: Claude 3 (Opus, Sonnet, Haiku)
- Google: Gemini Pro, Gemini Ultra
- GitHub Models: via models.inference.ai.azure.com
- Azure OpenAI: via *.openai.azure.com
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from adapters.base import ModelAdapter, ModelAdapterError, ModelConfig, ModelResponse

logger = logging.getLogger(__name__)


class APIModelAdapter(ModelAdapter):
    """Adapter for API-based models (OpenAI, Anthropic, etc.).

    Usage:
        config = ModelConfig(
            model_id="gpt-4",
            backend="openai",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        adapter = APIModelAdapter(config)
        response = adapter.generate("What is 2+2?")
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize API client based on backend."""
        if self.config.backend == "openai":
            self._initialize_openai()
        elif self.config.backend == "anthropic":
            self._initialize_anthropic()
        elif self.config.backend == "google":
            self._initialize_google()
        else:
            raise ModelAdapterError(f"Unsupported API backend: {self.config.backend}")

    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai

            self._client = openai.OpenAI(
                api_key=self.config.api_key, base_url=self.config.api_base, timeout=self.config.timeout
            )
            logger.info("OpenAI client initialized: model=%s", self.config.model_id)
        except ImportError:
            raise ModelAdapterError("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise ModelAdapterError(f"Failed to initialize OpenAI client: {e}")

    def _initialize_anthropic(self):
        """Initialize Anthropic client."""
        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self.config.api_key, timeout=self.config.timeout)
            logger.info("Anthropic client initialized: model=%s", self.config.model_id)
        except ImportError:
            raise ModelAdapterError("anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            raise ModelAdapterError(f"Failed to initialize Anthropic client: {e}")

    def _initialize_google(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.config.api_key)
            self._client = genai.GenerativeModel(self.config.model_id)
            logger.info("Google Gemini client initialized: model=%s", self.config.model_id)
        except ImportError:
            raise ModelAdapterError("google-generativeai package not installed. Run: pip install google-generativeai")
        except Exception as e:
            raise ModelAdapterError(f"Failed to initialize Google client: {e}")

    def generate(
        self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs
    ) -> ModelResponse:
        """Generate text completion via API."""
        start_time = time.time()

        # Use config defaults if not overridden
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature

        try:
            if self.config.backend == "openai":
                response = self._generate_openai(prompt, max_tokens, temperature, **kwargs)
            elif self.config.backend == "anthropic":
                response = self._generate_anthropic(prompt, max_tokens, temperature, **kwargs)
            elif self.config.backend == "google":
                response = self._generate_google(prompt, max_tokens, temperature, **kwargs)
            else:
                raise ModelAdapterError(f"Unsupported backend: {self.config.backend}")

            # Update stats
            self.call_count += 1
            self.total_tokens += response.total_tokens
            self.total_latency_ms += response.latency_ms

            return response

        except Exception as e:
            logger.error("API generation failed: model=%s error=%s", self.config.model_id, e)
            raise ModelAdapterError(f"Generation failed: {e}") from e

    async def generate_async(
        self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs
    ) -> ModelResponse:
        """Async generation (placeholder - would use async clients in production)."""
        # For now, fall back to sync
        return self.generate(prompt, max_tokens, temperature, **kwargs)

    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> ModelResponse:
        """Generate using OpenAI API."""
        start_time = time.time()

        try:
            completion = self._client.chat.completions.create(
                model=self.config.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=self.config.top_p,
                **kwargs,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return ModelResponse(
                model_id=self.config.model_id,
                content=completion.choices[0].message.content,
                prompt_tokens=completion.usage.prompt_tokens,
                completion_tokens=completion.usage.completion_tokens,
                total_tokens=completion.usage.total_tokens,
                latency_ms=latency_ms,
                finish_reason=completion.choices[0].finish_reason,
                metadata={"backend": "openai"},
            )
        except Exception as e:
            raise ModelAdapterError(f"OpenAI generation failed: {e}")

    def _generate_anthropic(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> ModelResponse:
        """Generate using Anthropic API."""
        start_time = time.time()

        try:
            message = self._client.messages.create(
                model=self.config.model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            return ModelResponse(
                model_id=self.config.model_id,
                content=message.content[0].text,
                prompt_tokens=message.usage.input_tokens,
                completion_tokens=message.usage.output_tokens,
                total_tokens=message.usage.input_tokens + message.usage.output_tokens,
                latency_ms=latency_ms,
                finish_reason=message.stop_reason,
                metadata={"backend": "anthropic"},
            )
        except Exception as e:
            raise ModelAdapterError(f"Anthropic generation failed: {e}")

    def _generate_google(self, prompt: str, max_tokens: int, temperature: float, **kwargs) -> ModelResponse:
        """Generate using Google Gemini API."""
        start_time = time.time()

        try:
            response = self._client.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": self.config.top_p,
                },
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Google doesn't return token counts in response (need to estimate)
            prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
            completion_tokens = len(response.text.split()) * 1.3

            return ModelResponse(
                model_id=self.config.model_id,
                content=response.text,
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                total_tokens=int(prompt_tokens + completion_tokens),
                latency_ms=latency_ms,
                finish_reason="stop",
                metadata={"backend": "google"},
            )
        except Exception as e:
            raise ModelAdapterError(f"Google generation failed: {e}")


# Example usage
if __name__ == "__main__":
    import os

    # OpenAI example
    config = ModelConfig(
        model_id="gpt-3.5-turbo", backend="openai", api_key=os.getenv("OPENAI_API_KEY"), max_tokens=100
    )

    adapter = APIModelAdapter(config)
    response = adapter.generate("What is 2+2?")

    print(f"Model: {response.model_id}")
    print(f"Response: {response.content}")
    print(f"Tokens: {response.total_tokens}")
    print(f"Latency: {response.latency_ms}ms")

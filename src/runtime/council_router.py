"""Council of Teachers - Role-Based Multi-Model Router.

AID: /src/runtime/council_router.py
Proof ID: PRF-COUNCIL-RTR-001

This module implements a sophisticated routing system that dispatches tasks to
specialized LLMs based on their strengths. Instead of using a single model,
the Council Router maintains a roster of 15+ frontier models and intelligently
selects the best "specialist" for each cognitive task.

Architecture:
- DEAN: Deep reasoning, logic, paradox generation (O1, DeepSeek R1, Claude 3.7)
- ENGINEER: Code, architecture, implementation (Claude 3.5, Mistral Large, Llama 405B)
- ARBITER: Grading, safety, judgment (Nemotron Reward, GPT-4o, Gemini 1.5 Pro)
- TA: Speed tasks, formatting, simple operations (Llama 3.3, Gemini Flash, Haiku)

Usage:
    router = CouncilRouter()
    paradox = router.route_request("DEAN", "Generate a Level 7 paradox...")
    grade = router.route_request("ARBITER", f"Grade this: {paradox}")
"""

from __future__ import annotations

import os
import random
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CouncilRouter:
    """Multi-model router with role-based specialist selection.
    
    Attributes:
        roster: Mapping of roles to lists of specialized model IDs
        client: OpenAI-compatible client (OpenRouter universal socket)
        fallback_model: Default model when specialists fail
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Council Router.
        
        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
        """
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            logger.error("Failed to import openai SDK: %s", e)
            raise RuntimeError("openai package required for CouncilRouter") from e

        # Universal Socket (OpenRouter)
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
        )
        
        # The Roster - Map Roles to Model IDs
        # Each role contains multiple models for rotation/fallback
        self.roster: Dict[str, List[str]] = {
            # Tier 1: Deep Reasoning & Logic (Level 7 Paradoxes)
            "DEAN": [
                "openai/o1-mini",                 # Fast chain-of-thought
                "deepseek/deepseek-r1",           # Open-source reasoning
                "anthropic/claude-3.7-sonnet",    # Balanced & nuanced
                "openai/gpt-4o",                  # Reliable reasoning
            ],
            
            # Tier 2: Code & Technical Implementation
            "ENGINEER": [
                "anthropic/claude-3.5-sonnet",    # Best coding model
                "mistralai/mistral-large",        # Strict instruction following
                "meta-llama/llama-3.1-405b-instruct",  # Open-source leviathan
                "qwen/qwen-2.5-coder-32b-instruct",    # Code-tuned speed
            ],
            
            # Tier 3: Grading & Safety Arbitration
            "ARBITER": [
                "nvidia/llama-3.1-nemotron-70b-instruct",  # Trained to judge
                "openai/gpt-4o",                           # Reliable standard
                "google/gemini-pro-1.5",                   # 2M token context
            ],
            
            # Tier 4: Speed & Efficiency (Teaching Assistants)
            "TA": [
                "meta-llama/llama-3.3-70b-instruct",  # Fast & smart
                "deepseek/deepseek-chat",             # Cheap generalist
                "google/gemini-flash-1.5",            # Speed demon
                "anthropic/claude-3-haiku",           # Pure speed
            ],
        }
        
        # Fallback model when specialists fail
        self.fallback_model = "meta-llama/llama-3.3-70b-instruct"
        
        logger.info("Council Router initialized with %d roles and %d total models",
                    len(self.roster), sum(len(models) for models in self.roster.values()))

    def route_request(
        self,
        role: str,
        prompt: str,
        system_msg: str = "",
        temperature: Optional[float] = None,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> str:
        """Route a request to the best specialist for the given role.
        
        Args:
            role: Specialist role (DEAN, ENGINEER, ARBITER, TA)
            prompt: User prompt/task description
            system_msg: System message for role/context setting
            temperature: Override default temperature for this role
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API
            
        Returns:
            Generated text response from the specialist model
            
        Raises:
            RuntimeError: If all models fail including fallback
        """
        # 1. Select the Model (Rotation Logic)
        # Pick randomly from the tier to prevent overfitting to one model's style
        available_models = self.roster.get(role, self.roster["TA"])
        model_id = random.choice(available_models)
        
        logger.info(">> Routing [%s] task to specialist: %s", role, model_id)

        # 2. Configure Special Parameters based on Role
        if temperature is None:
            if role == "ARBITER":
                temperature = 0.1  # Low temp for consistent judgment
            elif role == "DEAN":
                temperature = 0.8  # Higher for creative reasoning
            else:
                temperature = 0.7  # Balanced default

        # 3. Execute Call
        try:
            response = self._call_model(
                model_id=model_id,
                prompt=prompt,
                system_msg=system_msg,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            logger.info("[OK] [%s] completed via %s (%d chars)", 
                       role, model_id, len(response))
            return response
            
        except Exception as e:
            logger.warning("[ERROR] Error with %s: %s", model_id, e)
            # Fallback to a TA if the Specialist fails
            return self._fallback_call(prompt, system_msg, temperature, max_tokens)

    def _call_model(
        self,
        model_id: str,
        prompt: str,
        system_msg: str,
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> str:
        """Execute API call to specific model.
        
        Args:
            model_id: OpenRouter model identifier
            prompt: User prompt
            system_msg: System message
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional API parameters
            
        Returns:
            Generated text content
        """
        # Special handling for O1 (doesn't support system msg the same way)
        if "o1" in model_id or "o3" in model_id:
            messages = [{
                "role": "user",
                "content": f"{system_msg}\n\nTask: {prompt}" if system_msg else prompt
            }]
        else:
            messages = []
            if system_msg:
                messages.append({"role": "system", "content": system_msg})
            messages.append({"role": "user", "content": prompt})

        # OpenRouter API call with fallback support
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            # OpenRouter Specific: Auto-fallback if one is down
            extra_body={
                "provider": {
                    "allow_fallbacks": True
                }
            },
            **kwargs,
        )
        
        content = response.choices[0].message.content
        if content is None:
            raise ValueError(f"Model {model_id} returned empty content")
        return content

    def _fallback_call(
        self,
        prompt: str,
        system_msg: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Execute fallback call when primary specialist fails.
        
        Args:
            prompt: User prompt
            system_msg: System message
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            
        Returns:
            Generated text from fallback model
        """
        logger.warning("[FALLBACK] Engaging Fallback Protocol (%s)...", self.fallback_model)
        try:
            return self._call_model(
                model_id=self.fallback_model,
                prompt=prompt,
                system_msg=system_msg,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.error("[ERROR] Fallback model failed: %s", e)
            raise RuntimeError(f"All models failed including fallback: {e}") from e

    def get_roster(self, role: Optional[str] = None) -> Dict[str, List[str]]:
        """Get the current model roster.
        
        Args:
            role: Specific role to query (None returns all)
            
        Returns:
            Dictionary mapping roles to model lists
        """
        if role is None:
            return self.roster.copy()
        return {role: self.roster.get(role, [])}

    def add_model(self, role: str, model_id: str) -> None:
        """Add a model to a role's roster.
        
        Args:
            role: Role to add model to
            model_id: OpenRouter model identifier
        """
        if role not in self.roster:
            self.roster[role] = []
        if model_id not in self.roster[role]:
            self.roster[role].append(model_id)
            logger.info("Added %s to %s roster", model_id, role)

    def remove_model(self, role: str, model_id: str) -> bool:
        """Remove a model from a role's roster.
        
        Args:
            role: Role to remove model from
            model_id: OpenRouter model identifier
            
        Returns:
            True if model was removed, False if not found
        """
        if role in self.roster and model_id in self.roster[role]:
            self.roster[role].remove(model_id)
            logger.info("Removed %s from %s roster", model_id, role)
            return True
        return False


# Convenience function for quick usage
def create_council_router(api_key: Optional[str] = None) -> CouncilRouter:
    """Factory function to create a configured CouncilRouter instance.
    
    Args:
        api_key: OpenRouter API key (defaults to env var)
        
    Returns:
        Configured CouncilRouter instance
    """
    return CouncilRouter(api_key=api_key)

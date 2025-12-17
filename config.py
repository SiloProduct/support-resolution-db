"""Centralised application configuration.

Loads environment variables, exposes structured settings, and provides
helper utilities for LLM provider / model resolution.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List

from dotenv import load_dotenv

# Load variables from a .env file (if present) – same behaviour as env.py
load_dotenv(override=True)

# ---------------------------------------------------------------------------
# LLM provider & model registry
# ---------------------------------------------------------------------------

LLM_PROVIDERS: Dict[str, Dict[str, str]] = {
    "openai": {
        "api_key_env_var": "OPENAI_API_KEY",
    },
    "groq": {
        "api_key_env_var": "GROQ_API_KEY",
    },
    "gemini": {
        "api_key_env_var": "GEMINI_API_KEY",
    },
}

# List of supported models. Each entry maps a model name to its provider.
# The 'litellm_model' field is the model identifier used by litellm.
# The 'temperature' field is the default sampling temperature for the model.
AVAILABLE_MODELS: List[Dict] = [
    {"model": "gpt-4.1", "provider": "openai", "litellm_model": "gpt-4.1", "temperature": 0.2},
    {"model": "gpt-5.2", "provider": "openai", "litellm_model": "gpt-5.2", "temperature": 0.2},
    {"model": "moonshotai/kimi-k2-instruct", "provider": "groq", "litellm_model": "groq/moonshotai/kimi-k2-instruct", "temperature": 0.3},
    {"model": "openai/gpt-oss-120b", "provider": "groq", "litellm_model": "groq/openai/gpt-oss-120b", "temperature": 0.2},
    {"model": "gemini-3-pro-preview", "provider": "gemini", "litellm_model": "gemini/gemini-3-pro-preview", "temperature": 0.5},
]


@dataclass(frozen=True)
class LLMSettings:
    """Concrete settings resolved for a single model selection."""

    provider: str
    model: str
    litellm_model: str
    api_key: str
    temperature: float


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_llm_settings(model_name: str | None = None) -> LLMSettings:
    """Resolve provider details and API key for a given model.

    If *model_name* is ``None``, use the ``LLM_MODEL`` environment variable or
    fallback to the first entry in ``AVAILABLE_MODELS``.
    """

    if model_name is None:
        model_name = os.getenv("LLM_MODEL", AVAILABLE_MODELS[0]["model"])

    # Find model entry
    model_entry = next((m for m in AVAILABLE_MODELS if m["model"] == model_name), None)
    if not model_entry:
        available = ", ".join(m["model"] for m in AVAILABLE_MODELS)
        raise ValueError(f"Unknown LLM model '{model_name}'. Available: {available}")

    provider_key = model_entry["provider"]
    provider_cfg = LLM_PROVIDERS.get(provider_key)
    if provider_cfg is None:
        raise ValueError(f"No provider configuration for '{provider_key}'.")

    api_key_env = provider_cfg["api_key_env_var"]
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise KeyError(
            f"Missing environment variable '{api_key_env}' required for provider '{provider_key}'."
        )

    litellm_model = model_entry["litellm_model"]
    temperature = model_entry.get("temperature", 0.2)
    return LLMSettings(
        provider=provider_key,
        model=model_name,
        litellm_model=litellm_model,
        api_key=api_key,
        temperature=temperature,
    )


# Freshdesk / other global settings could be added here later 
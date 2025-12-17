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
        "base_url": "https://api.openai.com/v1/chat/completions",
    },
    "groq": {
        "api_key_env_var": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
    },
}

# List of supported models. Each entry maps a model name to its provider.
AVAILABLE_MODELS: List[Dict[str, str]] = [
    {"model": "gpt-4.1", "provider": "openai"},
    {"model": "gpt-5.2", "provider": "openai"},
    {"model": "moonshotai/kimi-k2-instruct", "provider": "groq"},
    {"model": "openai/gpt-oss-120b", "provider": "groq"},
]


@dataclass(frozen=True)
class LLMSettings:
    """Concrete settings resolved for a single model selection."""

    provider: str
    model: str
    api_key: str
    base_url: str

    def auth_header(self) -> Dict[str, str]:
        """Return Authorization header dict for HTTP calls."""

        return {"Authorization": f"Bearer {self.api_key}"}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_llm_settings(model_name: str | None = None) -> LLMSettings:
    """Resolve provider details, base URL and API key for a given model.

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

    base_url = provider_cfg["base_url"]
    return LLMSettings(provider=provider_key, model=model_name, api_key=api_key, base_url=base_url)


# Freshdesk / other global settings could be added here later 
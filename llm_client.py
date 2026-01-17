"""Minimal wrapper around LiteLLM for unified multi-provider LLM calls."""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional

import backoff
import litellm
from litellm.exceptions import RateLimitError, APIConnectionError, ServiceUnavailableError

from config import get_llm_settings

logger = logging.getLogger(__name__)

# Suppress litellm's verbose default logging
litellm.suppress_debug_info = True

# Set LiteLLM's logger to WARNING level by default to avoid breaking progress bars
# (can be overridden with --verbose flag)
litellm_logger = logging.getLogger("LiteLLM")
litellm_logger.setLevel(logging.WARNING)


@backoff.on_exception(
    backoff.expo,
    (RateLimitError, APIConnectionError, ServiceUnavailableError),
    max_tries=5,
)
def chat_completion(
    messages: List[Dict[str, str]],
    model_override: Optional[str] = None,
    temperature_override: Optional[float] = None,
) -> str:
    """Send chat completion request to the configured LLM provider via litellm.

    Parameters
    ----------
    messages : List[Dict[str, str]]
        Chat messages in OpenAI format.
    model_override : Optional[str], optional
        Specify an explicit model instead of using the ``LLM_MODEL`` env var.
    temperature_override : Optional[float], optional
        Override the model's default temperature. If None, uses the model's
        configured temperature from config.py.
    """

    llm_cfg = get_llm_settings(model_override)
    temperature = temperature_override if temperature_override is not None else llm_cfg.temperature

    # Set the API key for the provider in the environment (litellm reads from env)
    # This ensures litellm picks up the correct key for the provider
    if llm_cfg.provider == "openai":
        os.environ["OPENAI_API_KEY"] = llm_cfg.api_key
    elif llm_cfg.provider == "groq":
        os.environ["GROQ_API_KEY"] = llm_cfg.api_key
    elif llm_cfg.provider == "gemini":
        os.environ["GEMINI_API_KEY"] = llm_cfg.api_key

    logger.debug(
        "LLM request: model=%s, litellm_model=%s, temperature=%s, messages=%s",
        llm_cfg.model,
        llm_cfg.litellm_model,
        temperature,
        messages,
    )

    response = litellm.completion(
        model=llm_cfg.litellm_model,
        messages=messages,
        temperature=temperature,
    )

    # Log full response when in debug/verbose mode
    logger.debug("LLM raw response: %s", response)

    # Extract content from OpenAI-compatible response
    return response.choices[0].message.content.strip()

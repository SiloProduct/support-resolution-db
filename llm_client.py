"""Minimal wrapper around an OpenAI-compatible chat completion endpoint."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import backoff
import requests

from config import get_llm_settings

logger = logging.getLogger(__name__)


def _headers_for(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def chat_completion(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    model_override: Optional[str] = None,
) -> str:
    """Send chat completion request to the configured LLM provider.

    Parameters
    ----------
    messages : List[Dict[str, str]]
        Chat messages in OpenAI format.
    temperature : float, optional
        Sampling temperature, by default 0.2.
    model_override : Optional[str], optional
        Specify an explicit model instead of using the ``LLM_MODEL`` env var.
    """

    llm_cfg = get_llm_settings(model_override)

    payload = {
        "model": llm_cfg.model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    # Log the LLM request when verbose logging is enabled (no response logged)
    logger.debug("LLM request payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))

    resp = requests.post(
        llm_cfg.base_url,
        headers=_headers_for(llm_cfg.api_key),
        data=json.dumps(payload),
        timeout=60,
    )
    resp.raise_for_status()
    data: Dict[str, Any] = resp.json()

    # Log full response when in debug/verbose mode
    logger.debug("LLM raw response: %s", json.dumps(data, ensure_ascii=False, indent=2))

    # Assuming OpenAI-compatible response schema
    return data["choices"][0]["message"]["content"].strip() 
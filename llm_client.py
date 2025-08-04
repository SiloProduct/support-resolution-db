"""Minimal wrapper around an OpenAI-compatible chat completion endpoint."""
from __future__ import annotations

import json
import logging
from typing import Any, List, Dict

import backoff
import requests

from env import get

logger = logging.getLogger(__name__)

_BASE_URL = get("LLM_API_BASE_URL")
_API_KEY = get("LLM_API_KEY")
_MODEL = get("LLM_MODEL")

_HEADERS = {
    "Authorization": f"Bearer {_API_KEY}",
    "Content-Type": "application/json",
}

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def chat_completion(messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
    payload = {
        "model": _MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    # Log the LLM request when verbose logging is enabled (no response logged)
    logger.debug("LLM request payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))
    resp = requests.post(_BASE_URL, headers=_HEADERS, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    data: Dict[str, Any] = resp.json()
    # Assuming OpenAI format
    return data["choices"][0]["message"]["content"].strip() 
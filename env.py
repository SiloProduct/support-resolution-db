from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load variables from .env if present
load_dotenv(override=True)

_REQUIRED_VARS = [
    "FRESHDESK_DOMAIN",
    "FRESHDESK_API_KEY",
    "LLM_API_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
]


def get(key: str, default: Optional[str] = None) -> str:
    """Return an environment variable or raise if it's missing.

    Parameters
    ----------
    key : str
        Environment variable name.
    default : Optional[str]
        Fallback value if the variable is not set.
    """
    value = os.getenv(key, default)
    if value is None:
        raise KeyError(f"Missing required environment variable: {key}")
    return value


# Validate required variables eagerly at import time
for _var in _REQUIRED_VARS:
    _ = get(_var, None)

# Optional configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 3)) 
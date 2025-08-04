"""Fetch ticket IDs and conversations from Freshdesk."""
from __future__ import annotations

import base64
import logging
import time
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import quote_plus

import backoff
import requests
from tqdm import tqdm

from env import BATCH_SIZE, get

logger = logging.getLogger(__name__)

_DOMAIN = get("FRESHDESK_DOMAIN")
_API_KEY = get("FRESHDESK_API_KEY")

_BASE_URL = f"https://{_DOMAIN}.freshdesk.com/api/v2"

# Freshdesk uses basic auth with API_KEY as username and "X" as password.
_auth_token = base64.b64encode(f"{_API_KEY}:X".encode()).decode()
_HEADERS = {"Authorization": f"Basic {_auth_token}"}

# Minimum interval between calls (20 req/min → 3 s). Add a small cushion.
_MIN_INTERVAL = 3.2  # seconds
_last_call_ts = 0.0


def _rate_limit():
    """Block if the last Freshdesk call was less than _MIN_INTERVAL seconds ago."""
    global _last_call_ts
    elapsed = time.time() - _last_call_ts
    if elapsed < _MIN_INTERVAL:
        sleep_for = _MIN_INTERVAL - elapsed
        logger.debug("Rate limiting: sleeping %.2fs", sleep_for)
        time.sleep(sleep_for)


@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def _get_json(url: str) -> Any:
    """GET the given URL and return parsed JSON with retries and rate limiting."""
    while True:
        _rate_limit()
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "60"))
            logger.warning("Hit Freshdesk rate limit. Sleeping %ds", retry_after)
            time.sleep(retry_after)
            continue  # retry after waiting
        resp.raise_for_status()
        global _last_call_ts
        _last_call_ts = time.time()
        return resp.json()


def _search_url(page: int) -> str:
    # NOTE: Complex Lucene query – keep as-is but encode safely.
    query = "type:'Problem' AND created_at:>'2025-05-20' AND (status:4 OR status:5)"
    encoded = quote_plus(query)
    return f"{_BASE_URL}/search/tickets?query=\"{encoded}\"&page={page}"


def fetch_resolved_ticket_ids(max_pages: int = 5) -> List[int]:
    """Return a list of resolved/closed ticket IDs sorted by last update (oldest first)."""
    tickets: List[tuple[datetime, int]] = []
    for page in range(1, max_pages + 1):
        data = _get_json(_search_url(page))
        results = data.get("results", [])
        if not results:
            break
        for r in results:
            try:
                ts = datetime.strptime(r["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            except (KeyError, ValueError):
                ts = datetime.min
            tickets.append((ts, r["id"]))
    # Sort by timestamp ascending
    tickets.sort(key=lambda x: x[0])
    return [tid for _, tid in tickets]


def _conversation_url(ticket_id: int) -> str:
    return f"{_BASE_URL}/tickets/{ticket_id}?include=conversations"


def fetch_ticket(ticket_id: int) -> Dict[str, Any]:
    """Return full ticket including conversations."""
    return _get_json(_conversation_url(ticket_id))


def iter_tickets(ticket_ids: List[int], batch_size: int = BATCH_SIZE):
    """Yield ticket JSON objects, fetching in batches for progress visibility."""
    for i in range(0, len(ticket_ids), batch_size):
        batch = ticket_ids[i : i + batch_size]
        for tid in tqdm(batch, desc="Fetching conversations", leave=False):
            yield fetch_ticket(tid) 
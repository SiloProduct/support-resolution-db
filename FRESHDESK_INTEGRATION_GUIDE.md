# Freshdesk Ticket Fetching & Parsing Guide

> **Purpose**: This guide documents the reusable patterns for fetching and parsing Freshdesk tickets for LLM analysis projects. Use this as a reference when building similar applications with different filters, rules, or business logic.

---

## Overview

The Support Resolution DB app follows a multi-step flow:
1. **Fetch** ticket IDs from Freshdesk (with filters)
2. **Download** full ticket data (including conversations)
3. **Parse** and clean the raw ticket data
4. **Cache** conversations locally
5. **Process** with LLM for business logic (issue mapping, categorization, etc.)

This guide focuses on steps 1-4, which are highly reusable across different Freshdesk-based analysis tools.

---

## Architecture Components

### Key Files

| File | Purpose | Reusability |
|------|---------|-------------|
| `data_fetcher.py` | Freshdesk API interactions (fetch IDs, get conversations) | **High** - Core logic stays the same |
| `conversation_utils.py` | Parse & clean raw tickets, extract conversations | **Medium** - Adapt cleaning logic per use case |
| `env.py` | Environment variable management | **High** - Reuse as-is |
| `config.py` | Application configuration | **Medium** - Adapt for your settings |

---

## 1. Environment Setup

### Required Environment Variables

```python
# In .env file:
FRESHDESK_DOMAIN=your-domain      # e.g., "heysilo-help"
FRESHDESK_API_KEY=your_api_key    # Freshdesk API token

# Optional:
BATCH_SIZE=3                       # Number of tickets to fetch at once
```

### Loading Environment Variables

```python
# env.py pattern - validates required vars at import time
from dotenv import load_dotenv
import os

load_dotenv(override=True)

_REQUIRED_VARS = ["FRESHDESK_DOMAIN", "FRESHDESK_API_KEY"]

def get(key: str, default: str | None = None) -> str:
    """Return an environment variable or raise if missing."""
    value = os.getenv(key, default)
    if value is None:
        raise KeyError(f"Missing required environment variable: {key}")
    return value

# Validate eagerly at import
for _var in _REQUIRED_VARS:
    _ = get(_var, None)

BATCH_SIZE = int(os.getenv("BATCH_SIZE", 3))
```

---

## 2. Freshdesk API Integration

### Authentication

Freshdesk uses **HTTP Basic Auth** with API key as username and "X" as password:

```python
import base64

_DOMAIN = get("FRESHDESK_DOMAIN")
_API_KEY = get("FRESHDESK_API_KEY")
_BASE_URL = f"https://{_DOMAIN}.freshdesk.com/api/v2"

# Create auth token
_auth_token = base64.b64encode(f"{_API_KEY}:X".encode()).decode()
_HEADERS = {"Authorization": f"Basic {_auth_token}"}
```

### Rate Limiting

**Critical**: Freshdesk has a strict rate limit (20 requests/minute for most plans).

```python
import time

_MIN_INTERVAL = 3.2  # seconds (20 req/min → 3s + cushion)
_last_call_ts = 0.0

def _rate_limit():
    """Block if the last call was too recent."""
    global _last_call_ts
    elapsed = time.time() - _last_call_ts
    if elapsed < _MIN_INTERVAL:
        sleep_for = _MIN_INTERVAL - elapsed
        time.sleep(sleep_for)
```

### HTTP Requests with Retry Logic

Use exponential backoff for resilience:

```python
import backoff
import requests

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=5)
def _get_json(url: str) -> Any:
    """GET with rate limiting and retry on 429."""
    while True:
        _rate_limit()
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        
        # Handle 429 (rate limit exceeded)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "60"))
            logger.warning("Hit rate limit. Sleeping %ds", retry_after)
            time.sleep(retry_after)
            continue
        
        resp.raise_for_status()
        global _last_call_ts
        _last_call_ts = time.time()
        return resp.json()
```

---

## 3. Fetching Ticket IDs

### Search API Pattern

The Freshdesk Search API uses Lucene query syntax:

```python
from urllib.parse import quote_plus

def _search_url(page: int) -> str:
    # Build your query based on your needs
    # Common fields: type, created_at, updated_at, status, priority, tags
    query = "type:'Problem' AND created_at:>'2025-05-20' AND (status:4 OR status:5)"
    
    # IMPORTANT: URL-encode the query
    encoded = quote_plus(query)
    return f"{_BASE_URL}/search/tickets?query=\"{encoded}\"&page={page}"
```

### Common Query Patterns

```python
# Examples of different filters you might use:

# Resolved/Closed tickets after a date
"type:'Problem' AND created_at:>'2025-05-20' AND (status:4 OR status:5)"

# High priority tickets
"priority:3 AND status:2"  # 2=Open, 3=High

# Tickets with specific tags
"tag:'bug' OR tag:'feature-request'"

# Tickets from specific group
"group_id:12345 AND created_at:>'2025-01-01'"

# Combination with exclusions
"type:'Incident' AND NOT tag:'automated' AND status:5"
```

### Status Codes Reference

| Status | Code | Common Use |
|--------|------|------------|
| Open | 2 | Active tickets |
| Pending | 3 | Waiting on customer/agent |
| Resolved | 4 | Fixed, awaiting confirmation |
| Closed | 5 | Fully resolved |

### Fetching Ticket IDs with Pagination

```python
from datetime import datetime
from typing import List

def fetch_resolved_ticket_ids(max_pages: int = 5) -> List[int]:
    """Return list of ticket IDs, sorted by update time (oldest first)."""
    tickets: List[tuple[datetime, int]] = []
    
    for page in range(1, max_pages + 1):
        data = _get_json(_search_url(page))
        results = data.get("results", [])
        
        # Empty results = no more pages
        if not results:
            break
        
        for r in results:
            try:
                # Parse timestamp for sorting
                ts = datetime.strptime(r["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            except (KeyError, ValueError):
                ts = datetime.min
            tickets.append((ts, r["id"]))
    
    # Sort by timestamp ascending (oldest first)
    tickets.sort(key=lambda x: x[0])
    return [tid for _, tid in tickets]
```

**Note**: Freshdesk returns 30 tickets per page by default.

---

## 4. Fetching Full Ticket Data

### Get Single Ticket with Conversations

```python
def _conversation_url(ticket_id: int) -> str:
    # IMPORTANT: include=conversations parameter fetches all replies
    return f"{_BASE_URL}/tickets/{ticket_id}?include=conversations"

def fetch_ticket(ticket_id: int) -> Dict[str, Any]:
    """Return full ticket including conversations."""
    return _get_json(_conversation_url(ticket_id))
```

### Batch Iterator for Progress Tracking

```python
from tqdm import tqdm

def iter_tickets(ticket_ids: List[int], batch_size: int = 3):
    """Yield ticket JSON objects, fetching in batches for progress visibility."""
    for i in range(0, len(ticket_ids), batch_size):
        batch = ticket_ids[i : i + batch_size]
        for tid in tqdm(batch, desc="Fetching conversations", leave=False):
            yield fetch_ticket(tid)
```

---

## 5. Parsing Ticket Data

### Raw Ticket Structure

A Freshdesk ticket (with `?include=conversations`) has this structure:

```json
{
  "id": 123,
  "subject": "Issue with device",
  "description": "<div>HTML description...</div>",
  "description_text": "Plain text description",
  "status": 5,
  "priority": 1,
  "created_at": "2025-06-20T10:00:00Z",
  "updated_at": "2025-06-21T15:30:00Z",
  "custom_fields": {
    "cf_some_field": "value"
  },
  "conversations": [
    {
      "id": 456,
      "body": "<div>HTML reply...</div>",
      "body_text": "Plain text reply",
      "incoming": true,          // true = from customer, false = from agent
      "private": false,          // internal note vs public reply
      "created_at": "2025-06-20T11:00:00Z"
    }
  ]
}
```

### Text Cleaning Utilities

```python
import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CTRL_CHAR_RE = re.compile(r"[\r\x0b\x0c]")

def _clean_text(text: str) -> str:
    """Remove HTML tags and control characters, trim whitespace."""
    text_no_html = _HTML_TAG_RE.sub("", text or "")
    text_no_ctrl = _CTRL_CHAR_RE.sub("", text_no_html)
    return text_no_ctrl.strip()
```

### Building Conversation Object

```python
def build_conversation(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw ticket into clean conversation structure."""
    ticket_id = ticket["id"]
    messages: List[Dict[str, Any]] = []
    
    # First message: ticket description
    if ticket.get("description_text"):
        messages.append({
            "speaker": "user",
            "text": _clean_text(ticket["description_text"])
        })
    
    # Subsequent messages: conversations sorted chronologically
    for conv in sorted(ticket.get("conversations", []), key=lambda x: x["created_at"]):
        speaker = "user" if conv.get("incoming", False) else "agent"
        messages.append({
            "speaker": speaker,
            "text": _clean_text(conv.get("body_text", "")),
            "private": conv.get("private", False),
        })
    
    return {
        "ticket_id": ticket_id,
        "conversation": messages,
        "ignore": False  # For filtering logic (see below)
    }
```

### Unicode Normalization

For consistent text matching (e.g., matching phrases with curly quotes):

```python
def _normalize_apostrophes(text: str) -> str:
    """Normalize various apostrophe characters to straight apostrophe."""
    return (text
        .replace("\u2019", "'")  # right single quotation mark (')
        .replace("\u2018", "'")  # left single quotation mark (')
        .replace("\u02bc", "'")  # modifier letter apostrophe (ʼ)
        .replace("\u2032", "'")  # prime (′)
    )
```

---

## 6. Filtering & Ignore Logic

### Auto-Ignore Pattern

Exclude tickets with automated system messages (e.g., follow-ups, merges):

```python
AUTO_IGNORE_PHRASES = [
    "We wanted to check in since we haven't heard back from you",
    "This ticket is closed and merged",
]

def should_auto_ignore(messages: List[Dict[str, Any]]) -> bool:
    """Check if last message is an automated agent message."""
    if not messages:
        return False
    
    last_msg = messages[-1]
    if last_msg.get("speaker") != "agent":
        return False
    
    text = _normalize_apostrophes(last_msg.get("text", ""))
    return any(phrase in text for phrase in AUTO_IGNORE_PHRASES)
```

### Custom Field Filtering

Use Freshdesk custom fields for manual flagging:

```python
def build_conversation(ticket: Dict[str, Any]) -> Dict[str, Any]:
    # ... (build messages as above) ...
    
    ignore = False
    
    # Check custom field flag (set by support agents)
    custom_fields = ticket.get("custom_fields", {})
    if custom_fields.get("cf_ignore_from_analysis") is True:
        ignore = True
    
    # Also check automated messages
    if not ignore:
        ignore = should_auto_ignore(messages)
    
    return {
        "ticket_id": ticket_id,
        "conversation": messages,
        "ignore": ignore
    }
```

---

## 7. Caching Conversations

### Local JSON Cache Pattern

```python
from pathlib import Path
import json

CONVERSATIONS_DIR = Path("conversations")
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

def save_conversation(conv: Dict[str, Any]) -> Path:
    """Save conversation to local cache."""
    path = CONVERSATIONS_DIR / f"{conv['ticket_id']}.json"
    with path.open("w", encoding="utf-8") as fp:
        json.dump(conv, fp, ensure_ascii=False, indent=2)
    return path

def load_conversation(ticket_id: int) -> Dict[str, Any] | None:
    """Return cached conversation if it exists, else None."""
    path = CONVERSATIONS_DIR / f"{ticket_id}.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    return None

def is_ignored(ticket_id: int) -> bool:
    """Check if a conversation is marked as ignored."""
    conv = load_conversation(ticket_id)
    if conv is None:
        return False
    return conv.get("ignore", False)
```

### Cache-First Fetching Strategy

```python
def process_tickets(ticket_ids: List[int], refresh: bool = False):
    """Process tickets with caching logic."""
    for tid in ticket_ids:
        # Try cache first (unless refresh forced)
        conv = None
        if not refresh:
            conv = load_conversation(tid)
        
        # Fetch from API if not cached or refresh requested
        if conv is None or refresh:
            ticket_json = fetch_ticket(tid)
            conv = build_conversation(ticket_json)
            save_conversation(conv)
        
        # Skip ignored tickets
        if conv.get("ignore", False):
            logger.debug("Ticket %d is ignored, skipping", tid)
            continue
        
        # Process with your business logic here
        process_with_llm(conv)
```

---

## 8. Backfill & Migration Utilities

### Adding New Fields to Existing Cache

When you add new fields to your conversation structure:

```python
def ensure_ignore_flag(conv: Dict[str, Any]) -> bool:
    """Ensure conversation has 'ignore' flag, default to False.
    
    Returns True if flag was added (conversation modified).
    """
    if "ignore" not in conv:
        conv["ignore"] = False
        return True
    return False

def backfill_ignore_flags() -> tuple[int, int]:
    """Add 'ignore: false' to all conversations missing the flag.
    
    Returns (total_checked, total_updated) counts.
    """
    total_checked = 0
    total_updated = 0
    
    for path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as fp:
                conv = json.load(fp)
            total_checked += 1
            
            if ensure_ignore_flag(conv):
                with path.open("w", encoding="utf-8") as fp:
                    json.dump(conv, fp, ensure_ascii=False, indent=2)
                total_updated += 1
        except (json.JSONDecodeError, IOError):
            continue
    
    return total_checked, total_updated
```

### Retroactive Auto-Ignore Detection

Apply new ignore rules to existing conversations:

```python
def backfill_auto_ignore() -> tuple[int, int]:
    """Apply auto-ignore logic to all existing conversations.
    
    Returns (total_checked, total_auto_ignored) counts.
    """
    total_checked = 0
    total_auto_ignored = 0
    
    for path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as fp:
                conv = json.load(fp)
            total_checked += 1
            
            # Skip already ignored
            if conv.get("ignore", False):
                continue
            
            messages = conv.get("conversation", [])
            if should_auto_ignore(messages):
                conv["ignore"] = True
                with path.open("w", encoding="utf-8") as fp:
                    json.dump(conv, fp, ensure_ascii=False, indent=2)
                total_auto_ignored += 1
        except (json.JSONDecodeError, IOError):
            continue
    
    return total_checked, total_auto_ignored
```

---

## 9. Main Processing Loop

### Complete Flow Pattern

```python
from tqdm import tqdm
import logging

def run(pages: int, refresh: bool = False):
    """Complete ticket processing flow."""
    logging.basicConfig(level=logging.INFO)
    
    # Step 1: Fetch ticket IDs from Freshdesk
    logging.info("Fetching ticket IDs...")
    ticket_ids = fetch_resolved_ticket_ids(pages)
    logging.info(f"{len(ticket_ids)} tickets to process")
    
    # Step 2: Process each ticket
    for tid in tqdm(ticket_ids, desc="Processing tickets"):
        # Load or fetch conversation (with caching)
        conv = None
        if not refresh:
            conv = load_conversation(tid)
        
        if conv is None or refresh:
            ticket_json = fetch_ticket(tid)
            conv = build_conversation(ticket_json)
            save_conversation(conv)
        
        # Skip ignored tickets
        if conv.get("ignore", False):
            logging.debug(f"Ticket {tid} is ignored, skipping")
            continue
        
        # Your business logic here
        # e.g., LLM processing, categorization, etc.
        process_conversation(conv)
```

---

## 10. Best Practices & Tips

### Rate Limiting
- **Always implement rate limiting** - Freshdesk is strict (20 req/min)
- Add extra cushion (3.2s instead of 3.0s) for safety
- Handle 429 responses with `Retry-After` header
- Use exponential backoff for transient errors

### Caching
- **Cache aggressively** - Freshdesk API calls are expensive
- Store conversations as JSON files (one per ticket)
- Use ticket ID as filename for easy lookup
- Implement `refresh` flag for forced re-fetching

### Error Handling
- Wrap API calls with try-except and continue on errors
- Log failures but don't crash the entire batch
- Consider retry logic with backoff for network errors

### Performance
- Fetch in batches with progress bars (tqdm)
- Process tickets as they're fetched (streaming)
- Don't load all tickets into memory at once

### Data Quality
- Always use `description_text` and `body_text` (not HTML versions)
- Clean text thoroughly (remove HTML tags, control chars)
- Normalize Unicode characters for consistent matching
- Sort conversations chronologically before processing

### Filtering
- Implement multiple ignore mechanisms (auto + manual)
- Use custom fields for agent-driven exclusions
- Document your ignore phrases clearly
- Make ignore logic reversible (store flag, don't delete)

### Testing
- Start with small page counts (1-2 pages = 30-60 tickets)
- Use `--ticket-ids` flag to test specific problematic tickets
- Implement `--prompt-debug` mode to see LLM I/O without writing DB
- Test rate limiting with high-volume batches

---

## 11. Adapting for New Projects

### Checklist for New Freshdesk Analysis Apps

When building a new app with different business logic:

**✓ Reuse as-is:**
- [ ] `env.py` - Environment variable management
- [ ] `data_fetcher.py` - Core API interaction (auth, rate limiting, fetch)
- [ ] Text cleaning utilities from `conversation_utils.py`

**⚙️ Adapt to your needs:**
- [ ] **Search query** - Modify `_search_url()` for your filters
  - Change ticket types (Problem, Incident, Question)
  - Adjust date ranges
  - Add/remove status codes
  - Include custom field filters
  
- [ ] **Ignore logic** - Customize `AUTO_IGNORE_PHRASES` and custom fields
  - Add your domain-specific automated messages
  - Define relevant custom field flags
  
- [ ] **Conversation structure** - Extend `build_conversation()` output
  - Add fields from ticket metadata (priority, tags, custom fields)
  - Include additional conversation attributes
  - Add preprocessing specific to your LLM needs
  
- [ ] **Business logic** - Replace issue clustering with your processing
  - Classification, sentiment analysis, topic modeling, etc.
  - Different LLM prompts and workflows
  - Different output formats

**📝 Configure:**
- [ ] Update `.env` with your Freshdesk credentials
- [ ] Adjust `BATCH_SIZE` based on your rate limit
- [ ] Define your output directory structure
- [ ] Set up logging appropriate to your needs

---

## 12. Code Snippets Reference

### Quick Start Template

```python
# minimal_freshdesk_fetcher.py
from __future__ import annotations
import os, base64, time, json
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import quote_plus

load_dotenv()

# Setup
DOMAIN = os.getenv("FRESHDESK_DOMAIN")
API_KEY = os.getenv("FRESHDESK_API_KEY")
BASE_URL = f"https://{DOMAIN}.freshdesk.com/api/v2"
AUTH = base64.b64encode(f"{API_KEY}:X".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}"}

last_call = 0.0
MIN_INTERVAL = 3.2

def rate_limit():
    global last_call
    elapsed = time.time() - last_call
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    last_call = time.time()

def get_json(url: str):
    rate_limit()
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_tickets(query: str, max_pages: int = 5):
    """Fetch tickets matching Lucene query."""
    tickets = []
    for page in range(1, max_pages + 1):
        encoded = quote_plus(query)
        url = f'{BASE_URL}/search/tickets?query="{encoded}"&page={page}'
        data = get_json(url)
        results = data.get("results", [])
        if not results:
            break
        tickets.extend(results)
    return tickets

def get_ticket_with_conversations(ticket_id: int):
    """Fetch full ticket including all replies."""
    url = f"{BASE_URL}/tickets/{ticket_id}?include=conversations"
    return get_json(url)

# Example usage
if __name__ == "__main__":
    # Fetch resolved tickets from last 6 months
    tickets = fetch_tickets("created_at:>'2024-07-01' AND status:5", max_pages=2)
    print(f"Found {len(tickets)} tickets")
    
    # Get full conversation for first ticket
    if tickets:
        full = get_ticket_with_conversations(tickets[0]["id"])
        Path("output").mkdir(exist_ok=True)
        Path("output/sample.json").write_text(json.dumps(full, indent=2))
```

---

## 13. Freshdesk API Resources

### Official Documentation
- [Freshdesk API v2 Docs](https://developers.freshdesk.com/api/)
- [Search API](https://developers.freshdesk.com/api/#search)
- [Tickets API](https://developers.freshdesk.com/api/#tickets)
- [Rate Limiting](https://developers.freshdesk.com/api/#ratelimit)

### Common Endpoints
```python
# List tickets (paginated, max 30 per page)
GET /api/v2/tickets?page={page}

# Search tickets (Lucene syntax)
GET /api/v2/search/tickets?query="{encoded_query}"

# Get single ticket
GET /api/v2/tickets/{id}

# Get ticket with conversations
GET /api/v2/tickets/{id}?include=conversations

# Get ticket with requester info
GET /api/v2/tickets/{id}?include=requester

# Get ticket with stats
GET /api/v2/tickets/{id}?include=stats
```

### Lucene Query Syntax Quick Reference
```python
# Exact match
"type:'Problem'"

# Date ranges
"created_at:>'2025-01-01'"
"updated_at:<'2025-12-31'"

# Status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
"status:5"

# Priority (1=Low, 2=Medium, 3=High, 4=Urgent)
"priority:3"

# Boolean operators
"type:'Bug' AND status:4"
"priority:3 OR priority:4"
"type:'Question' AND NOT tag:'faq'"

# Combinations
"(status:4 OR status:5) AND created_at:>'2025-06-01'"
```

---

## Summary

This guide covers the complete Freshdesk integration pattern used in the Support Resolution DB app. The core fetching and parsing logic is highly reusable - adapt the search queries, ignore logic, and output structure to match your specific use case while keeping the robust API handling, rate limiting, and caching infrastructure.

**Key Takeaways:**
1. Always implement rate limiting (3.2s between calls)
2. Cache aggressively to avoid redundant API calls
3. Use `description_text` and `body_text` (not HTML)
4. Implement flexible ignore logic (auto + manual)
5. Handle errors gracefully with retries and backoff
6. Sort conversations chronologically
7. Store conversations as individual JSON files
8. Use Lucene syntax for powerful search queries

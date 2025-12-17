"""Transform Freshdesk ticket JSON into a clean conversation object."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CTRL_CHAR_RE = re.compile(r"[\r\x0b\x0c]")

# Automated agent messages that indicate the ticket should be ignored
AUTO_IGNORE_PHRASES = [
    "We wanted to check in since we haven't heard back from you",
    "This ticket is closed and merged",
]


def _normalize_apostrophes(text: str) -> str:
    """Normalize curly apostrophes to straight apostrophes for consistent matching."""
    # Replace various Unicode apostrophe/quote characters with straight apostrophe
    # Using explicit Unicode escapes to avoid encoding issues:
    # \u2019 = right single quotation mark (')
    # \u2018 = left single quotation mark (')
    # \u02bc = modifier letter apostrophe (ʼ)
    # \u2032 = prime (′)
    return (text
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u02bc", "'")
        .replace("\u2032", "'")
    )

CONVERSATIONS_DIR = Path("conversations")
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _clean_text(text: str) -> str:
    """Remove HTML tags and control characters, trim whitespace."""
    text_no_html = _HTML_TAG_RE.sub("", text or "")
    text_no_ctrl = _CTRL_CHAR_RE.sub("", text_no_html)
    return text_no_ctrl.strip()


def should_auto_ignore(messages: List[Dict[str, Any]]) -> bool:
    """Check if a conversation should be auto-ignored based on the last message.
    
    Returns True if the last message is from an agent and contains one of the
    automated system message phrases (e.g., follow-up check-ins or merge notices).
    """
    if not messages:
        return False
    
    last_msg = messages[-1]
    if last_msg.get("speaker") != "agent":
        return False
    
    # Normalize apostrophes for consistent matching (curly → straight)
    text = _normalize_apostrophes(last_msg.get("text", ""))
    return any(phrase in text for phrase in AUTO_IGNORE_PHRASES)


def build_conversation(ticket: Dict[str, Any]) -> Dict[str, Any]:
    """Return the simplified conversation object described in the requirements."""
    ticket_id = ticket["id"]
    messages: List[Dict[str, Any]] = []

    # First message from description_text
    if ticket.get("description_text"):
        messages.append({"speaker": "user", "text": _clean_text(ticket["description_text"])})

    for conv in sorted(ticket.get("conversations", []), key=lambda x: x["created_at"]):
        speaker = "user" if conv.get("incoming", False) else "agent"
        messages.append(
            {
                "speaker": speaker,
                "text": _clean_text(conv.get("body_text", "")),
                "private": conv.get("private", False),
            }
        )

    # Auto-ignore tickets with automated system messages as last message
    ignore = should_auto_ignore(messages)
    return {"ticket_id": ticket_id, "conversation": messages, "ignore": ignore}


def save_conversation(conv: Dict[str, Any]) -> Path:
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


def ensure_ignore_flag(conv: Dict[str, Any]) -> bool:
    """Ensure the conversation has an 'ignore' flag, defaulting to False.
    
    Returns True if the flag was added (conversation was modified).
    """
    if "ignore" not in conv:
        conv["ignore"] = False
        return True
    return False


def backfill_ignore_flags() -> tuple[int, int]:
    """Add 'ignore: false' to all conversations that don't have the flag.
    
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


def is_ignored(ticket_id: int) -> bool:
    """Check if a conversation is marked as ignored."""
    conv = load_conversation(ticket_id)
    if conv is None:
        return False
    return conv.get("ignore", False)


def backfill_auto_ignore() -> tuple[int, int]:
    """Apply auto-ignore logic to all existing conversations.
    
    Checks each conversation and sets ignore=True if it matches the auto-ignore
    criteria (last message is an automated agent message). Does NOT un-ignore
    conversations that were manually ignored for other reasons.
    
    Returns (total_checked, total_auto_ignored) counts.
    """
    total_checked = 0
    total_auto_ignored = 0
    
    for path in CONVERSATIONS_DIR.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as fp:
                conv = json.load(fp)
            total_checked += 1
            
            # Skip if already ignored
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
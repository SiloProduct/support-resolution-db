"""Transform Freshdesk ticket JSON into a clean conversation object."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_CTRL_CHAR_RE = re.compile(r"[\r\x0b\x0c]")

CONVERSATIONS_DIR = Path("conversations")
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _clean_text(text: str) -> str:
    """Remove HTML tags and control characters, trim whitespace."""
    text_no_html = _HTML_TAG_RE.sub("", text or "")
    text_no_ctrl = _CTRL_CHAR_RE.sub("", text_no_html)
    return text_no_ctrl.strip()


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

    return {"ticket_id": ticket_id, "conversation": messages, "ignore": False}


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
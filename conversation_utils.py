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

    return {"ticket_id": ticket_id, "conversation": messages}


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
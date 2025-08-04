"""Maintain the issue database and interact with LLM for classification."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

from llm_client import chat_completion
from prompts_config import SYSTEM_PROMPT, USER_TEMPLATE

_OUTPUT_DIR = Path("output")
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class IssueClusterer:
    def __init__(self, load_existing: bool = True):
        self.issues: List[Dict[str, Any]] = []
        if load_existing:
            self._load()

    # -------------------- Query helpers --------------------
    def has_ticket(self, ticket_id: int) -> bool:
        """Return True if ticket_id is already present in the DB."""
        return any(ticket_id in issue.get("tickets", []) for issue in self.issues)

    # -------------------- Persistence --------------------
    _DB_PATH = _OUTPUT_DIR / "silo_issues_db.json"

    def _load(self):
        if self._DB_PATH.exists():
            self.issues = json.loads(self._DB_PATH.read_text())

    def save(self, path: str | Path | None = None):
        out_path = Path(path) if path else self._DB_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(self.issues, ensure_ascii=False, indent=2))

    # -------------------- Processing --------------------
    def _issues_summary(self) -> str:
        summary_lines = []
        for issue in self.issues:
            short_desc = issue.get("short_description", "")
            root_cause = issue.get("root_cause", "")
            keywords = ", ".join(issue.get("keywords", []))
            summary_lines.append(
                f"{issue['issue_id']}: {issue.get('category', '')} / {short_desc} / {root_cause} | {keywords}"
            )
        return "\n".join(summary_lines) or "<none>"

    def process_conversation(self, conv: Dict[str, Any], debug: bool = False):
        user_prompt = USER_TEMPLATE.format(
            issues_summary=self._issues_summary(),
            conversation=json.dumps(conv, ensure_ascii=False, indent=2),
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ]
        if debug:
            print("\n--- SYSTEM MESSAGE ---\n" + messages[0]["content"])
            print("\n--- USER MESSAGE ---\n" + messages[1]["content"])

        response = chat_completion(messages)

        if debug:
            print("\n--- RAW LLM RESPONSE ---\n" + response)
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # fallback: treat as low confidence new issue
            parsed = {
                "issue_id": None,
                "category": "unknown",
                "keywords": [],
                "root_cause": "",
                "resolution_steps": [],
                "confidence": 0.0,
                "notes": response,
            }
        if debug:
            print("\n--- PARSED JSON ---\n" + json.dumps(parsed, ensure_ascii=False, indent=2))

        self._merge(parsed, conv["ticket_id"])

    # -------------------- Merge Logic --------------------
    def _merge(self, issue_data: Dict[str, Any], ticket_id: int):
        if issue_data.get("confidence", 0) < 0.7 or not issue_data.get("issue_id"):
            # Invent new ID
            new_id = f"ISSUE-{len(self.issues)+1:04d}"
            issue_data["issue_id"] = new_id
            issue_data["tickets"] = [ticket_id]
            self.issues.append(issue_data)
            return

        # Find existing issue
        for issue in self.issues:
            if issue["issue_id"] == issue_data["issue_id"]:
                # Update existing issue with latest details (replace fields except "tickets")
                for key, value in issue_data.items():
                    if key != "tickets":
                        issue[key] = value
                issue.setdefault("tickets", [])
                if ticket_id not in issue["tickets"]:
                    issue["tickets"].append(ticket_id)
                return

        # If not found, treat as new
        issue_data["tickets"] = [ticket_id]
        self.issues.append(issue_data) 
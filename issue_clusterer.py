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
    def __init__(self, load_existing: bool = True, db_path: Path | None = None):
        self._db_path: Path = Path(db_path) if db_path else Path("output/silo_issues_db.json")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self.issues: List[Dict[str, Any]] = []
        if load_existing and self._db_path.exists():
            self._load()

    # -------------------- Query helpers --------------------
    def has_ticket(self, ticket_id: int) -> bool:
        """Return True if ticket_id is already present in the DB."""
        return any(ticket_id in issue.get("tickets", []) for issue in self.issues)

    # -------------------- Persistence --------------------
    def _load(self):
        self.issues = json.loads(self._db_path.read_text()) if self._db_path.exists() else []

    def save(self, path: str | Path | None = None):
        out_path = Path(path) if path else self._db_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(self.issues, ensure_ascii=False, indent=2))

    # -------------------- Processing --------------------
    def _issues_summary(self) -> str:
        summary_lines = []
        for issue in self.issues:
            short_desc = issue.get("short_description", "")
            root_cause = issue.get("root_cause", "")
            keywords = ", ".join(issue.get("keywords", []))
            tickets = ", ".join(str(tid) for tid in issue.get("tickets", []))
            summary_lines.append(
                f"{issue['issue_id']}: {issue.get('category', '')} / {short_desc} / {root_cause} | {keywords} | Linked tickets: {tickets}"
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
        # -----------------------------------------------
        # Helper: generate next sequential ISSUE-XXXX id
        # -----------------------------------------------
        def _next_issue_id() -> str:
            max_num = 0
            for iss in self.issues:
                try:
                    num = int(iss["issue_id"].split("-")[-1])
                    max_num = max(max_num, num)
                except (KeyError, ValueError):
                    continue
            return f"ISSUE-{max_num + 1:04d}"

        # If low confidence or missing id -> treat as new, *unless* this ticket already exists
        if issue_data.get("confidence", 0) < 0.7 or not issue_data.get("issue_id"):
            for iss in self.issues:
                if ticket_id in iss.get("tickets", []):
                    # Update existing issue instead of creating duplicate
                    iss.setdefault("tickets", [])
                    # Copy over any improved details from issue_data
                    for key, val in issue_data.items():
                        if key != "tickets" and val:
                            iss[key] = val
                    return

            # Otherwise invent new ID
            new_id = _next_issue_id()
            issue_data["issue_id"] = new_id
            issue_data["tickets"] = [ticket_id]
            self.issues.append(issue_data)
            return

        # Find existing issue by id
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
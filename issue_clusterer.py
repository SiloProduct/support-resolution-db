"""Maintain the issue database and interact with LLM for classification."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from llm_client import chat_completion
from prompts_config import get_system_prompt, USER_TEMPLATE

logger = logging.getLogger(__name__)

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
            {"role": "system", "content": get_system_prompt().strip()},
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

        # -----------------------------------------------
        # Helper: generate next branch id for a parent issue_id
        # e.g., "ISSUE-0001" -> "ISSUE-0001-1", "ISSUE-0001-2", etc.
        # Also supports branching from branches: "ISSUE-0001-1" -> "ISSUE-0001-1-1"
        # -----------------------------------------------
        def _next_branch_id(parent_id: str) -> str:
            prefix = f"{parent_id}-"
            max_branch = 0
            for iss in self.issues:
                iss_id = iss.get("issue_id", "")
                if iss_id.startswith(prefix):
                    # Extract the immediate branch number (first segment after parent)
                    suffix = iss_id[len(prefix):]
                    # Get only the first segment (in case of nested branches like "1-1")
                    first_segment = suffix.split("-")[0]
                    try:
                        branch_num = int(first_segment)
                        max_branch = max(max_branch, branch_num)
                    except ValueError:
                        continue
            return f"{parent_id}-{max_branch + 1}"

        # -----------------------------------------------
        # Helper: find the insertion index for a branched issue
        # Branches should be placed after their parent and any existing branches
        # -----------------------------------------------
        def _find_branch_insert_index(parent_id: str) -> int:
            parent_idx = -1
            last_related_idx = -1
            prefix = f"{parent_id}-"
            
            for idx, iss in enumerate(self.issues):
                iss_id = iss.get("issue_id", "")
                if iss_id == parent_id:
                    parent_idx = idx
                    last_related_idx = idx
                elif iss_id.startswith(prefix):
                    last_related_idx = idx
            
            # Insert after the last related entry (parent or sibling branch)
            if last_related_idx >= 0:
                return last_related_idx + 1
            # If parent not found, append at end
            return len(self.issues)

        # -----------------------------------------------
        # Case 1: No issue_id returned -> treat as new issue
        # -----------------------------------------------
        if not issue_data.get("issue_id"):
            # Check if this ticket already exists in the DB
            for iss in self.issues:
                if ticket_id in iss.get("tickets", []):
                    # Update existing issue instead of creating duplicate
                    iss.setdefault("tickets", [])
                    for key, val in issue_data.items():
                        if key != "tickets" and val:
                            iss[key] = val
                    logger.debug("Ticket %d already in DB, updated existing issue %s", ticket_id, iss["issue_id"])
                    return

            # Create new issue with sequential ID
            new_id = _next_issue_id()
            issue_data["issue_id"] = new_id
            issue_data["tickets"] = [ticket_id]
            self.issues.append(issue_data)
            logger.info("Created new issue %s for ticket %d (no issue_id from LLM)", new_id, ticket_id)
            return

        # -----------------------------------------------
        # Case 2: issue_id returned with LOW confidence (< 0.9)
        # -> Create a branch entry instead of updating
        # -----------------------------------------------
        confidence = issue_data.get("confidence", 0)
        returned_issue_id = issue_data.get("issue_id")
        
        if confidence < 0.9:
            # Check if this ticket already exists in the DB
            for iss in self.issues:
                if ticket_id in iss.get("tickets", []):
                    # Update existing issue instead of creating duplicate branch
                    iss.setdefault("tickets", [])
                    for key, val in issue_data.items():
                        if key != "tickets" and val:
                            iss[key] = val
                    logger.debug("Ticket %d already in DB, updated existing issue %s", ticket_id, iss["issue_id"])
                    return

            # Create a new branch entry
            branch_id = _next_branch_id(returned_issue_id)
            issue_data["issue_id"] = branch_id
            issue_data["tickets"] = [ticket_id]
            
            # Insert at the correct position (after parent and existing branches)
            insert_idx = _find_branch_insert_index(returned_issue_id)
            self.issues.insert(insert_idx, issue_data)
            logger.info(
                "Created branch issue %s from %s for ticket %d (confidence %.2f < 0.9)",
                branch_id, returned_issue_id, ticket_id, confidence
            )
            return

        # -----------------------------------------------
        # Case 3: issue_id returned with HIGH confidence (>= 0.9)
        # -> Update the existing entry
        # -----------------------------------------------
        for issue in self.issues:
            if issue["issue_id"] == returned_issue_id:
                # Update existing issue with latest details (replace fields except "tickets")
                for key, value in issue_data.items():
                    if key != "tickets":
                        issue[key] = value
                issue.setdefault("tickets", [])
                if ticket_id not in issue["tickets"]:
                    issue["tickets"].append(ticket_id)
                logger.info("Updated existing issue %s with ticket %d (confidence %.2f)", returned_issue_id, ticket_id, confidence)
                return

        # If not found, treat as new (keep the LLM-assigned issue_id)
        issue_data["tickets"] = [ticket_id]
        self.issues.append(issue_data)
        logger.info("Created new issue %s for ticket %d (LLM-assigned ID not found in DB)", returned_issue_id, ticket_id) 
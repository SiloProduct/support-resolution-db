# Implementation Plan – Silo Support Ticket Issue Clustering

## 1. Objectives
- Fetch ~150 resolved/closed Freshdesk tickets (5 pages × 30 tickets/page default).
- Build cleaned conversation objects for each ticket.
- Use an LLM to (a) decide whether a ticket represents a **new issue** or matches an **existing issue**, and (b) output metadata needed for a consolidated `silo_issues_db.json`.
- Flag tickets whose classification confidence is low for human review.

## 2. Proposed Repository Structure
```text
project/
├── main.py                # Orchestrates full flow (CLI entrypoint)
├── data_fetcher.py        # Freshdesk HTTP helpers (ticket IDs, conversations)
├── conversation_utils.py  # Cleans & structures raw ticket+conversation data
├── llm_client.py          # Thin wrapper around chosen chat-completion API
├── issue_clusterer.py     # Maintains issue DB, interacts with LLM, handles dedup/merge
├── prompts_config.py      # Prompt templates & formatting utilities
├── env.py                 # Loads & validates environment variables
├── requirements.txt       # Python deps (see Section 8)
├── conversations/         # Persisted cleaned conversations JSON, one per ticket
└── output/
    └── silo_issues_db.json
```

## 3. Environment & Configuration
- Read all secrets from a **.env** file (not committed) via `python-dotenv`.
- Required variables (from RequirementsDoc):
  - `FRESHDESK_DOMAIN`
  - `FRESHDESK_API_KEY`
  - `LLM_API_BASE_URL`
  - `LLM_API_KEY`
  - `LLM_MODEL`
  - `BATCH_SIZE` (default 3)
- Provide `env.py` with a `get(key, default=None)` helper and validation on startup.

## 4. Data Retrieval Flow (`data_fetcher.py`)
1. **Fetch Ticket IDs**
   - Endpoint: `/api/v2/search/tickets?query="status:3 OR status:4"&page=N`.
   - Iterate `page=1..5` (configurable; loop until empty results to future-proof).
   - Store list of IDs and basic ticket metadata (status, subject) for logs.

2. **Batch Fetch Conversations**
   - Process IDs in batches of `BATCH_SIZE` (3).
   - Endpoint: `/api/v2/tickets/{ticketId}?include=conversations`.
   - Respect Freshdesk rate limits: 
     - Add `time.sleep()` or exponential backoff on HTTP 429.
   - Return raw JSON per ticket.

## 5. Conversation Structuring (`conversation_utils.py`)
- For each ticket JSON:
  1. Grab `description_text` as first user message if `source` originated from requester.
  2. Iterate over `conversations` array sorted by `created_at`.
  3. Map each item to:
     ```json
     {"speaker": "user"|"agent", "text": <body_text>, "private": <bool>, "incoming": <bool>}
     ```
  4. Collapse consecutive messages from same speaker to reduce prompt size.
  5. Strip HTML artifacts, trim whitespace.
  6. Persist cleaned object to `conversations/{ticket_id}.json` for reference.
- Return object conforming to RequirementsDoc format.

## 6. LLM Interaction (`llm_client.py` & `issue_clusterer.py`)
### 6.1 llm_client.py
- Generic `chat(messages, **kwargs)` that hits `LLM_API_BASE_URL`.
- Automatic retry on transient HTTP errors or 429.
- Log `prompt_tokens`, `completion_tokens` for cost tracking.

### 6.2 Prompts (`prompts_config.py`)
- System prompt: *You are a support issue classifier...* (draft separately).
- User prompt template inputs:
  - Current conversation (JSON or formatted text)
  - Current state of issue DB (list of existing `category`+`keywords`)
- Expected model output (JSON schema):
  ```json
  {
    "issue_id": "<string>|null",  # null if new issue
    "category": "<string>",
    "keywords": ["..."],
    "root_cause": "...",
    "resolution_steps": ["..."],
    "confidence": 0-1,
    "notes": "..."  # optional
  }
  ```

### 6.3 issue_clusterer.py
- Maintains in-memory list + dict keyed by `issue_id`.
- For each conversation:
  1. Send LLM prompt.
  2. If `issue_id` returned is null **or** `confidence < 0.7`, create new provisional issue.
  3. Else, append ticket ID to existing issue.
  4. Persist intermediate state every N tickets → `output/silo_issues_db.tmp.json` for crash safety.

## 7. Final Output
- After all tickets processed, write deterministic, sorted JSON file to `output/silo_issues_db.json`.
- Also emit `flagged_for_review.csv` listing ticket IDs with `confidence < 0.7`.
- Cleaned conversations are available under `conversations/` for auditing.

## 8. Dependencies (`requirements.txt`)
```
requests>=2.32.4
python-dotenv>=1.1.1
tqdm>=4.67.1
backoff>=2.2.1
```
(Add any LLM SDK if needed, else raw `requests`).

## 9. Logging & Observability
- Use Python `logging` with stdout handler.
- Levels: INFO for progress, DEBUG for HTTP payloads when `--verbose` flag.

## 10. CLI Usage (`main.py`)
```bash
python -m main --pages 5 --batch-size 3 --output output/silo_issues_db.json --verbose
```
- Argparse parameters allow overrides.

## 11. Testing Strategy
- Unit tests for:
  - URL building & pagination logic.
  - Conversation extraction edge cases (no conversations, merged tickets, HTML stripping).
- Mock LLM responses using fixtures to ensure deterministic tests.

## 12. Future Enhancements
- Persist issue DB in SQLite for incremental runs.
- Add embeddings & semantic search to pre-filter candidate issues before LLM call (cost savings).
- Parallelize conversation fetches with `concurrent.futures` respecting rate limits.

## 13. Timeline (Effort Estimate)
1. Repo scaffolding & env loader – 0.5 day
2. Data fetcher implementation & tests – 1 day
3. Conversation utilities – 0.5 day
4. LLM client + prompts – 1 day
5. issue_clusterer logic – 1 day
6. Integration, logging, manual run – 0.5 day
7. Documentation & README – 0.5 day
**Total ~5 days** 

## 14. Manual Ticket Seeding & Prompt Iteration

We need a workflow that bypasses automatic ticket-ID fetching so we can:
1. Seed the initial issues DB with hand-picked tickets.
2. Rapidly iterate on prompt designs without processing 150+ tickets.

### 14.1 CLI Enhancements (main.py)
- `--ticket-ids 123,456,789`  
  • Comma-separated list of IDs. When provided, **skip** `fetch_resolved_ticket_ids` and process only these IDs in order.  
  • Compatible with `--pages`; mutual-exclusive group.
- `--prompt-debug`  
  • Do not update the DB. Instead, print:  
    – Rendered `system` and `user` messages.  
    – Raw LLM JSON response.  
    – Parsed dict.  
  • Returns exit-code 0 so it can be used in unit tests.

### 14.2 Data Path
The same internal functions (`fetch_ticket`, `build_conversation`) are reused; only the ID source changes. This keeps logic DRY.

### 14.3 Seeding Workflow
```bash
python -m main --ticket-ids 169,167,166 --output output/seed.json
```
After inspection, rename `seed.json` to `silo_issues_db.json` (or merge manually) and commit it to version control as the starting DB for production.

### 14.4 Testing Strategy
1. **Unit tests** (pytest):
   • Patch `llm_client.chat_completion` to return deterministic JSON.  
   • Call `run(ticket_ids=[123])` and assert that `issue_clusterer` contains expected entry.  
   • Call with `--prompt-debug` and assert no DB writes.
2. **Integration smoke test**
   • Use `--prompt-debug` against a real ticket ID with `LLM_API_KEY` set and verify that JSON parses without exceptions.

### 14.5 Code Changes Summary
- Modify `main.py` argparse: add mutually-exclusive group `--pages` vs `--ticket-ids`.
- `run()` accepts optional `ticket_ids: List[int] | None`.
- In `run()`: if `ticket_ids` provided → use that; else call `fetch_resolved_ticket_ids`.
- Implement `--prompt-debug` flag: wrap DB update block in `if not args.prompt_debug:`.
- Update `IssueClusterer.save()` call accordingly.
- Extend README/docs with seeding instructions. 
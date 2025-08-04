# Silo Support Ticket Issue Clustering

A command-line utility that fetches resolved/closed Freshdesk tickets, cleans their conversation history, and uses a Large-Language Model to cluster them into a consolidated issue database.

---

## Features

• Batch-fetch ticket conversations via the Freshdesk API

• Cleans/normalizes conversations and stores them under `conversations/`

• Sends conversations to an LLM which decides if the ticket matches an existing issue or should create a new one

• Maintains an evergreen JSON issue database (`output/silo_issues_db.json`)

• Flag low-confidence classifications for human review

---

## Quick Start

```bash
# 1. Clone and create a virtual env
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create a .env file (see below)

# 4. Run against the latest 5 pages of resolved tickets
python -m main --pages 5
```

---

## Environment Variables (`.env`)

The tool relies on the following **required** variables:

| Variable | Description |
|----------|-------------|
| `FRESHDESK_DOMAIN` | Your Freshdesk sub-domain, e.g. `heysilo-help` |
| `FRESHDESK_API_KEY` | Freshdesk API token with read access |
| `LLM_API_BASE_URL` | Base URL for the chat-completion endpoint |
| `LLM_API_KEY` | API key for the LLM provider |
| `LLM_MODEL` | Model name (e.g. `gpt-4o`) |

Optional:

| Variable | Default | Description |
|-----------|---------|-------------|
| `BATCH_SIZE` | `3` | Number of tickets fetched in parallel from Freshdesk |

> The application aborts at startup if any required variable is missing.

---

## CLI Usage

Run the script with `python -m main [FLAGS]`.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--pages` | `int` | `5` | Number of pages of resolved tickets to fetch (30 tickets per page). Mutually exclusive with `--ticket-ids`. |
| `--ticket-ids` | `str` | _None_ | Comma-separated list of ticket IDs to process manually. Skips the automatic ID search. Mutually exclusive with `--pages`. |
| `--batch-size` | `int` | value of `BATCH_SIZE` env var (or `3`) | Size of each Freshdesk fetch batch. Overrides env var when supplied. |
| `--output` | `path` | `output/silo_issues_db.json` | Location where the consolidated issue DB is written. |
| `--prompt-debug` | _flag_ | _False_ | Print the fully-rendered system & user prompts, the raw LLM JSON response, and the parsed object **without writing** to the issue DB. Useful for prompt iteration. |
| `--reprocess` | _flag_ | _False_ | Re-run the LLM on tickets already present in the database (uses cached conversation unless `--refresh` is also set). |
| `--refresh` | _flag_ | _False_ | Re-fetch conversations from Freshdesk before processing (can be combined with `--reprocess`). |
| `--verbose` | _flag_ | _False_ | Enable debug-level logging (HTTP payloads, retries, token counts). |

Example – prompt debugging a single ticket:

```bash
python -m main \
  --ticket-ids 226 \
  --prompt-debug \
  --verbose \
  --output tmp/seed.json
```

---

## Folder Structure (important paths)

```
project/
├── main.py                # CLI entrypoint
├── data_fetcher.py        # Freshdesk HTTP helpers
├── conversation_utils.py  # Cleans & structures raw ticket data
├── issue_clusterer.py     # Maintains issue DB, interacts with LLM
├── prompts_config.py      # Prompt templates
├── env.py                 # Environment loader & validation
├── conversations/         # Cleaned conversation JSON files
└── output/                # Final issue DB & temp files
```

---

## Development & Testing

1. Install dev dependencies (pytest, etc.)
2. Run unit tests:

```bash
pytest -q
```

3. Run a smoke test against a real ticket in **prompt-debug** mode to ensure parsing works.

---

## Troubleshooting

* **KeyError: Missing required environment variable** – verify your `.env` file is present and contains all required keys.
* **HTTP 429 Too Many Requests** – Freshdesk rate-limited. The script has exponential backoff; wait or lower `BATCH_SIZE`.

---

## Future Enhancements

See `plan.md` §12 for roadmap items like SQLite persistence, embeddings-based pre-filtering, and concurrency improvements. 
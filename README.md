# Silo Support Ticket Issue CLI

A command-line tool that fetches Freshdesk tickets, cleans their conversations and clusters them into an **ever-green JSON issue database** – powered by an LLM.

---

## 1 · Features

* **Modern Typer CLI** with sub-commands & rich help text
* **Interactive wizard** (ticket source ➜ processing options ➜ model picker ➜ confirmation)
* Flag-based **non-interactive** mode for automation/CI
* Pluggable multi-provider LLM support (OpenAI, Groq …)
* Safe-output mode (`--safe-output`) to avoid accidental DB overwrites
* Progress bars (tqdm) & colourful tables (Rich)
* Exponential back-off for both Freshdesk & LLM HTTP calls

---

## 2 · Quick Start

```bash
# 1 · Create & activate a virtual environment
python -m venv .venv && source .venv/bin/activate

# 2 · Install deps
pip install -r requirements.txt

# 3 · Create .env with the required keys (see below)

# 4 · Run in *interactive* mode (recommended for first run)
python -m cli process
```

Non-interactive example (latest 3 pages, overwrite DB):

```bash
python -m cli process --pages 3 --verbose
```

---

## 3 · Environment Variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `FRESHDESK_DOMAIN` | ✅ | e.g. `heysilo-help` |
| `FRESHDESK_API_KEY` | ✅ | Freshdesk API token |
| `OPENAI_API_KEY` | *optional* | Required when using an OpenAI model |
| `GROQ_API_KEY` | *optional* | Required when using a Groq-hosted model |
| `BATCH_SIZE` | 🚫 | Default fetch batch size (`3`) |
| `LLM_MODEL` | 🚫 | Default model when `--model` flag is omitted |

**Secrets** stay only in `.env`; the repo never stores keys.

---

## 4 · CLI Reference

### `process` – The work-horse

```
python -m cli process [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--pages <int>` | `5` | Fetch *n* pages of the latest resolved tickets (30 tickets / page). Mutually exclusive with `--ticket-ids`. |
| `--ticket-ids <CSV>` | – | Comma-separated list of ticket IDs to process manually. |
| `--batch-size <int>` | env `BATCH_SIZE` | Override fetch batch size. |
| `--model <name>` | env `LLM_MODEL` or first entry in `config.AVAILABLE_MODELS` | Specify the LLM model. |
| `--reprocess / --no-reprocess` | `False` | Re-run LLM even if ticket already in DB. |
| `--refresh / --no-refresh` | `False` | Re-download conversations from Freshdesk. |
| `--safe-output / --no-safe-output` | `False` | If enabled and writing to the default DB, the script will **copy** the original DB to `silo_issues_db_YYYYMMDD_HHMMSS.json` and update that copy instead of overwriting. |
| `--output <path>` | `output/silo_issues_db.json` | Custom output path. |
| `--non-interactive` | – | Skip the interactive wizard. Provide ticket flags or `--pages` when using this. |
| `--prompt-debug` | – | Print prompts/LLM responses without writing DB. |
| `--verbose` | – | Debug-level logging for HTTP payloads & token counts. |

*Running without ticket flags & without `--non-interactive` automatically launches the wizard.*

### `config` sub-command

```bash
python -m cli config show
```
Shows current configuration, effective default model and presence of provider API keys (masked).

---

## 5 · Interactive Workflow ✨

1. **Select tickets** – latest pages *or* manual list.
2. **Choose options** – `Reprocess` / `Refresh` via check-boxes.
3. **Pick model** – list derived from `config.AVAILABLE_MODELS`.
4. **Summary** – Rich table with parameters; confirm to proceed.

Everything else happens automatically.

---

## 6 · Developer Guide

### Folder Structure

```
project/
├── cli.py                 # Typer entry-point
├── main.py                # Legacy orchestration (still used internally)
├── config.py              # Central app & model config
├── env.py                 # Legacy env loader (Freshdesk only)
├── data_fetcher.py        # Freshdesk HTTP helpers
├── conversation_utils.py  # Cleans & structures raw ticket data
├── issue_clusterer.py     # Maintains issue DB & interacts with LLM
└── output/                # Final issue DB & temp copies
```

### Tests

```bash
pip install -r requirements.txt   # pytest included
pytest -q
```

---

## 7 · Safety & Compliance

* All secrets remain in `.env` (git-ignored).
* `--safe-output` prevents accidental DB corruption.
* Exponential back-off for API resilience.
* Semantic versioning (current: `0.2.0`).

---

## 8 · Roadmap

See `plan.md` for the full implementation plan & future enhancements (SQLite backend, embeddings filter, Textual TUI, plugin system, …) 
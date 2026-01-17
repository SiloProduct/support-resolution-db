# Silo Support Ticket Issue CLI

A command-line tool that fetches Freshdesk tickets, cleans their conversations and clusters them into an **ever-green JSON issue database** – powered by an LLM.

---

## 1 · Features

* **Modern Typer CLI** with sub-commands & rich help text
* **Interactive wizard** (ticket source ➜ processing options ➜ model picker ➜ confirmation)
* Flag-based **non-interactive** mode for automation/CI
* **Unified LLM support** via LiteLLM (OpenAI, Groq, Google Gemini, and 100+ providers)
* **Per-model temperature configuration** for optimal results
* **Auto-ignore tickets** with automated system messages or agent-flagged custom fields
* **Support agent notes** loaded dynamically from `Support-agent-notes.txt` for context-aware analysis
* Safe-output mode (`--safe-output`) with model-specific test runs
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
| `GEMINI_API_KEY` | *optional* | Required when using a Google Gemini model |
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
| `--safe-output / --no-safe-output` | `False` | If enabled and writing to the default DB, the script will **copy** the original DB to `output/test-runs/silo_issues_db_YYYYMMDD_HHMMSS_<model>.json` and update that copy instead of overwriting. The model name is included in the filename for easy identification. |
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

## 4.1 · Model Configuration

Models are configured in `config.py` with per-model settings:

* **Model identifier** – Display name used in CLI
* **Provider** – LLM provider (openai, groq, gemini, etc.)
* **LiteLLM model name** – Provider-specific model identifier
* **Temperature** – Default sampling temperature (0.0-2.0)

Each model has its own optimal temperature setting. You can override the temperature per-call if needed, but the model defaults are tuned for best results.

### Supported Models

Currently configured models include:
* OpenAI: `gpt-4.1`, `gpt-5.2`
* Groq: `moonshotai/kimi-k2-instruct`, `openai/gpt-oss-120b`
* Google Gemini: `gemini-3-pro-preview`

To add more models, edit `config.AVAILABLE_MODELS` in `config.py`. LiteLLM supports 100+ providers, so adding new models is straightforward.

---

## 4.2 · Ignore Flags

Tickets can be automatically excluded from analysis via two mechanisms:

### Auto-Ignore (Automated System Messages)

Tickets are automatically flagged as ignored if the last message is from an agent and contains:
* `"We wanted to check in since we haven't heard back from you"`
* `"This ticket is closed and merged"`

These indicate follow-up messages or merged tickets that don't contain useful issue information.

### Custom Field Flag

Support agents can flag tickets via the Freshdesk custom field `cf_ignore_from_analysis`. When set to `true`, the ticket is automatically marked as ignored during fetch.

Ignored tickets are skipped during processing and won't appear in the issue database.

---

## 4.3 · Support Agent Notes

The tool automatically loads context from `Support-agent-notes.txt` and appends it to the system prompt. This allows the LLM to have up-to-date information about:

* Current software versions (device firmware, app versions)
* Hardware notes (common container issues, known problems)
* Setup procedures (Bluetooth vs Wi-Fi setup methods)

**Important:** Update `Support-agent-notes.txt` before running analysis to ensure the LLM has the latest context. The interactive wizard will remind you to check this file.

The notes are loaded dynamically at runtime, so changes take effect immediately without code modifications.

---

## 5 · Interactive Workflow ✨

1. **Reminder** – Check that `Support-agent-notes.txt` is up to date.
2. **Select tickets** – latest pages *or* manual list.
3. **Choose options** – `Reprocess` / `Refresh` via check-boxes.
4. **Pick model** – list derived from `config.AVAILABLE_MODELS` (each with optimized temperature).
5. **Summary** – Rich table with parameters; confirm to proceed.

Everything else happens automatically: fetching, caching, auto-ignore detection, LLM analysis, and database updates.

---

## 6 · Developer Guide

### Folder Structure

```
project/
├── cli.py                      # Typer entry-point
├── main.py                     # Legacy orchestration (still used internally)
├── config.py                   # Central app & model config (LLM providers, models, temperatures)
├── llm_client.py               # LiteLLM wrapper for unified multi-provider LLM calls
├── prompts_config.py            # LLM prompt templates & support notes loader
├── env.py                      # Legacy env loader (Freshdesk only)
├── data_fetcher.py             # Freshdesk HTTP helpers
├── conversation_utils.py        # Cleans & structures raw ticket data, ignore flag logic
├── issue_clusterer.py           # Maintains issue DB & interacts with LLM
├── Support-agent-notes.txt      # Dynamic context notes loaded into system prompt
├── conversations/               # Cached ticket conversations (JSON)
└── output/                      # Final issue DB
    ├── silo_issues_db.json      # Main database
    └── test-runs/               # Safe-output copies with model names
```

### LLM Integration

The tool uses [LiteLLM](https://github.com/BerriAI/litellm) for unified multi-provider LLM support. This provides:

* **Unified API** – Same interface for OpenAI, Groq, Google Gemini, and 100+ providers
* **Automatic retries** – Built-in exponential backoff and error handling
* **Consistent output** – Normalized responses across providers
* **Easy extensibility** – Add new providers by updating `config.py`

The `llm_client.py` module wraps LiteLLM with project-specific configuration (temperature, logging, etc.).

### Tests

```bash
pip install -r requirements.txt   # pytest included
pytest -q
```

---

## 7 · Safety & Compliance

* All secrets remain in `.env` (git-ignored).
* `--safe-output` prevents accidental DB corruption by creating timestamped copies in `output/test-runs/`.
* Ignore flags prevent processing of irrelevant tickets (follow-ups, merges, agent-flagged).
* Exponential back-off for API resilience.
* LiteLLM provides unified error handling and retry logic across all providers.
* Semantic versioning (current: `0.2.0`).

---

## 8 · Roadmap

See `plan.md` for the full implementation plan & future enhancements (SQLite backend, embeddings filter, Textual TUI, plugin system, …) 
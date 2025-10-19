# Implementation Plan – User-Friendly CLI Overhaul

_Last updated: 2025-08-06_

## 0. Objectives

1. Replace the current argparse-based entry-point with a modern, discoverable, and secure command-line interface.
2. Introduce an **interactive workflow** that lets users:
   • Select tickets (latest pages or explicit IDs)
   • Choose whether to **reprocess** and/or **refresh** conversations
   • Pick the **LLM provider + model** from a curated list (drawing the required API key name from the environment – never hard-coding secrets).
3. Keep non-interactive (flag-based) usage fully functional for power users and automation.
4. Centralise configuration (env + CLI overrides) in a single module.

---

## 1. Dependencies & Tooling

| Purpose                    | Library | Action |
|----------------------------|---------|--------|
| CLI framework              | `typer` | Add to `requirements.txt` |
| Rich-text output & tables  | `rich`  | Add to `requirements.txt` |
| Interactive prompts        | `questionary` (built on `prompt_toolkit`) | Add to `requirements.txt` |
| .env loading (already used)| `python-dotenv` | Ensure still present |

> All new deps are permissively licensed and widely adopted as of Aug 2025.

---

## 2. High-Level Command Topology

```
silo-cli (program name)
│
├─ process      # main ticket processor (interactive by default)
│   ├─ --pages <int>
│   ├─ --ticket-ids <list>
│   ├─ --batch-size <int>
│   ├─ --model <model_name>   # optional – bypass selector
│   ├─ --reprocess / --no-reprocess
│   ├─ --refresh / --no-refresh
│   ├─ --output <path>
│   └─ --non-interactive      # run with supplied flags only
│
└─ config        # view current effective configuration
    └─ show
```

* **Default behaviour**: running `silo-cli process` with no flags launches the interactive wizard.
* All sub-commands inherit global flags such as `--verbose`.

---

## 3. Interactive Flow (Wizard)

1. **Ticket Source**
   * Questionary `select` – «How would you like to choose tickets?»
     1. Latest resolved tickets (by pages)
     2. Enter ticket IDs manually
   * Subsequent prompt(s) capture the numeric value or comma-separated list.

2. **Processing Options** (`checkbox` prompt – multi-select)
   * Reprocess tickets already present in DB
   * Refresh conversations from Freshdesk

3. **LLM Model Selection**
   * Display each entry as `«model_name» (provider)` – e.g. `gpt-4o (openai)`.
   * Under the hood, each choice carries the provider + model identifier.

4. **Summary & Confirmation**
   * Rich renders a table summarising: ticket set, options, chosen model, destination DB path.
   * Questionary `confirm` – «Proceed?»

On confirmation, the CLI calls existing business logic (`run()` in `main.py`, eventually refactored) with the resolved parameters.

---

## 4. Configuration Refactor

1. **New Module**: `config.py`
   * Loads `.env` via `dotenv_values`.
   * Provides `AppConfig` dataclass with fields: Freshdesk creds, default batch size, list of available models, provider metadata, defaults.
   * Validates presence of secrets at startup (currently done in `env.py`; we’ll merge/replace).

2. **Model & Provider Registry** (moved out of code that uses it)
   ```python
   # config.py
   LLM_PROVIDERS = {
       "openai": {
           "api_key_env_var": "OPENAI_API_KEY",
           "base_url": "https://api.openai.com/v1",
       },
       "groq": {
           "api_key_env_var": "GROQ_API_KEY",
           "base_url": "https://api.groq.com/openai/v1",
       },
   }

   AVAILABLE_MODELS = [
       {"model": "gpt-4o", "provider": "openai"},
       {"model": "gpt-3.5-turbo", "provider": "openai"},
       {"model": "llama3-70b-8192", "provider": "groq"},
   ]
   ```
3. **Migration**: existing modules (`llm_client.py`, `issue_clusterer.py`) import provider info from `config.py` instead of hard-coded env names.

---

## 5. Code Refactor Roadmap

| Phase | Work Items | Owner | ETA |
|-------|------------|-------|-----|
| 1 | _Foundation_ – add deps & scaffold `cli.py` with Typer app shell. | dev | day 1 |
| 2 | Port current `main.run()` logic into a Typer `process()` command (non-interactive path). | dev | day 1 |
| 3 | Implement interactive wizard using Questionary + Rich + existing logic. | dev | day 2 |
| 4 | Create `config.py`; move env loading & model registry; update callers. | dev | day 2 |
| 5 | Write `config show` command (simple Rich table). | dev | day 3 |
| 6 | Update `README.md`: installation, new usage examples. | dev | day 3 |
| 7 | Unit tests for `config` and CLI commands using `typer.testing.CliRunner`. | dev | day 3 |

---

## 6. Security & Compliance Checklist

* **Secrets** only in `.env`; ensure `.env` remains in `.gitignore`.
* Validate that the chosen provider’s required env var is set; abort with clear error if missing.
* No network calls made during model selection – purely local metadata lookup.
* Follow semantic versioning; bump version to 0.2.0 with this breaking CLI change.

---

## 7. Open Questions / Future Enhancements

1. **Plugin System**: dynamic discovery of additional providers/models via entry-points.
2. **`db` Command Group**: inspect, export, or prune the issues DB.
3. **Auto-completion**: leverage Typer’s shell completion for models & providers.
4. **Textual-based TUI**: consider upgrading interactive mode to a full Rich-Textual UI in the future.

---

_This plan has been agreed upon by the team and serves as the single source of truth for the upcoming CLI overhaul. Any deviations require a pull-request against this document._ 
"""Typer-based command-line interface for the Support Ticket Issue tool.

This replaces the legacy argparse entry-point in ``main.py`` while
keeping backwards-compatible access to the same business logic.

Usage (dev):
    python -m cli process --pages 5
    python -m cli config show
"""
from __future__ import annotations

import logging
from pathlib import Path
import webbrowser
from typing import List, Optional, Dict

import typer
from rich.console import Console
from rich.table import Table

# Import the existing run() orchestration from main.py to avoid duplication
from main import run as legacy_run  # noqa: WPS433

app = typer.Typer(help="Silo Support Ticket Issue CLI")
console = Console()


@app.command("process")
def process_command(
    # Ticket selection (mutually exclusive)
    pages: int = typer.Option(
        None,
        "--pages",
        min=1,
        help="Number of pages of resolved tickets to fetch (30 tickets each).",
    ),
    ticket_ids: Optional[str] = typer.Option(
        None,
        "--ticket-ids",
        help="Comma-separated list of ticket IDs to process manually.",
    ),
    # Other processing options
    batch_size: Optional[int] = typer.Option(
        None, "--batch-size", help="Freshdesk fetch batch size override."
    ),
    output: Path = typer.Option(
        Path("output/silo_issues_db.json"),
        "--output",
        help="Output path for the consolidated issue DB.",
    ),
    safe_output: bool = typer.Option(
        False,
        "--safe-output/--no-safe-output",
        help="If enabled and the target DB exists, write to a timestamped copy instead of overwriting.",
    ),
    reprocess: bool = typer.Option(
        False, "--reprocess/--no-reprocess", help="Re-run LLM on cached tickets."
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh/--no-refresh",
        help="Re-fetch conversations from Freshdesk even if cached.",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable debug logging."),
    prompt_debug: bool = typer.Option(
        False,
        "--prompt-debug/--no-prompt-debug",
        help="Print prompts/LLM output without writing to DB.",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        help="LLM model identifier (overrides LLM_MODEL env var).",
    ),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Skip the interactive wizard (suitable for automation).",
    ),
):
    """Process tickets and update the issue database.

    If *non_interactive* is False and no explicit ticket selection flags were
    provided, an interactive wizard **will be added in a later phase**.
    For now, we delegate immediately to the legacy ``run()`` function.
    """

    # Validate mutual exclusivity manually because Typer can't enforce across
    # dynamic parameters very well.
    if pages and ticket_ids:
        typer.echo("Error: --pages and --ticket-ids are mutually exclusive.")
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Interactive wizard (only when user didn't supply ticket selection
    # flags and did not request --non-interactive)
    # ------------------------------------------------------------------

    # placeholder to hold parsed ids_list across code branches
    ids_list: Optional[List[int]] = None

    if not non_interactive and not pages and not ticket_ids:
        import questionary
        from rich import box

        # 1) Ticket source selection
        source = questionary.select(
            "How would you like to select tickets?",
            choices=[
                "Latest resolved tickets (by pages)",
                "Enter ticket IDs manually",
            ],
        ).ask()

        if source is None:
            raise typer.Exit(code=1)

        if source.startswith("Latest"):
            pages_str = questionary.text("Number of pages to fetch?", default="5").ask()
            if pages_str is None:
                raise typer.Exit(code=1)
            try:
                pages = max(1, int(pages_str))
            except ValueError:
                typer.echo("Invalid number, aborting.")
                raise typer.Exit(code=1)
            ids_list = None
        else:
            ids_raw = questionary.text("Enter comma-separated ticket IDs:").ask()
            if ids_raw is None:
                raise typer.Exit(code=1)
            try:
                ids_list = [int(i.strip()) for i in ids_raw.split(",") if i.strip()]
            except ValueError:
                typer.echo("Invalid ticket ID provided, aborting.")
                raise typer.Exit(code=1)
            pages = None

        # 2) Processing options
        opts = questionary.checkbox(
            "Select additional processing options:",
            choices=[
                questionary.Choice("Reprocess existing tickets", checked=False),
                questionary.Choice("Refresh conversations from Freshdesk", checked=False),
            ],
        ).ask()

        reprocess = "Reprocess existing tickets" in opts if opts else False
        refresh = "Refresh conversations from Freshdesk" in opts if opts else False

        # 3) Model selection
        from config import AVAILABLE_MODELS

        model_choice = questionary.select(
            "Select LLM model:",
            choices=[f"{m['model']} ({m['provider']})" for m in AVAILABLE_MODELS],
        ).ask()

        if model_choice is None:
            raise typer.Exit(code=1)
        model = model_choice.split(" ")[0]  # first token is model name

        # 4) Summary (always show for interactive mode)
        if not non_interactive and not pages and not ticket_ids:
            from rich.console import Console
            from rich.table import Table

            console_summary = Console()
            table = Table(title="Run Summary", box=box.SIMPLE)
            table.add_column("Parameter")
            table.add_column("Value")
            table.add_row("Ticket selection", source)
            table.add_row("Pages" if pages else "Ticket IDs", str(pages or ids_list))
            table.add_row("Reprocess", str(reprocess))
            table.add_row("Refresh", str(refresh))
            table.add_row("Model", model)
            table.add_row("Output", str(output))
            console_summary.print(table)

            proceed = questionary.confirm("Proceed with processing?", default=True).ask()
            if not proceed:
                typer.echo("Aborted.")
                raise typer.Exit(code=0)

    # ---------------- Safe-output handling for all modes -----------------
    default_db_path = Path("output/silo_issues_db.json")
    if safe_output and output == default_db_path and output.exists():
        from datetime import datetime

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = output.parent / f"silo_issues_db_{ts}.json"
        typer.echo(f"[info] Existing DB preserved. Writing to {output}")

        if default_db_path.exists():
            output.write_text(default_db_path.read_text())

    # --------------------------------------------------------------------

    # Parse ticket IDs list (comma separated string ➜ list[int]) only if not set
    if ids_list is None and ticket_ids:
        try:
            ids_list = [int(t.strip()) for t in ticket_ids.split(",") if t.strip()]
        except ValueError as exc:
            typer.echo(f"Invalid ticket ID in list: {exc}")
            raise typer.Exit(code=1)

    # Fallback default if neither flag is provided and non-interactive is used
    if non_interactive and not (pages or ticket_ids):
        pages = 5  # default from legacy CLI

    # Override model via env var if provided
    if model:
        import os  # local import to avoid at module top unnecessarily

        os.environ["LLM_MODEL"] = model

    # TODO: Phase-2 – invoke interactive wizard when appropriate.

    # Delegate to legacy implementation
    legacy_run(
        pages=pages or 5,
        batch_size=batch_size,
        output=output,
        verbose=verbose,
        ticket_ids=ids_list,
        prompt_debug=prompt_debug,
        reprocess=reprocess,
        refresh=refresh,
    )

    # ------------------------------------------------------------------
    # Guarantee the advertised output file exists (issue #safe-output)
    # If the processing loop skipped all tickets (e.g., already clustered),
    # legacy_run() logs success but doesn't create the file. In that case we
    # copy the existing DB (if any) or create an empty JSON array to the
    # new destination so the user is not confused.
    # ------------------------------------------------------------------
    if not output.exists():
        default_db_path = Path("output/silo_issues_db.json")
        if default_db_path.exists():
            output.write_text(default_db_path.read_text())
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("[]")
        typer.echo(f"[info] Created placeholder DB at {output} (no new tickets)")


# ------------- config command group -------------
config_app = typer.Typer(help="Inspect configuration values.")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show():
    """Display effective configuration loaded from environment variables."""

    # Lazy import to avoid circular deps until we refactor env ➜ config.
    import env  # noqa: WPS433
    import os

    from config import AVAILABLE_MODELS, LLM_PROVIDERS

    table = Table(title="Effective Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    base_keys = [
        "FRESHDESK_DOMAIN",
        "FRESHDESK_API_KEY",
        "BATCH_SIZE",
    ]

    for key in base_keys:
        try:
            value = getattr(env, key) if hasattr(env, key) else env.get(key)
        except KeyError:
            value = "<missing>"
        if "KEY" in key and isinstance(value, str) and value != "<missing>":
            value = f"***{value[-4:]}"
        table.add_row(key, str(value))

    # Default / selected model
    default_model = os.getenv("LLM_MODEL", AVAILABLE_MODELS[0]["model"])
    table.add_row("LLM_MODEL (effective)", default_model)

    # Provider API keys presence
    for provider, meta in LLM_PROVIDERS.items():
        env_var = meta["api_key_env_var"]
        masked = "<missing>"
        if os.getenv(env_var):
            masked = "***" + os.getenv(env_var)[-4:]
        table.add_row(f"{provider} API key", masked)

    console.print(table)


# ------------------------------------------------------------
# config set command – update .env defaults
# ------------------------------------------------------------


def _update_env_file(**updates):
    """Update or create key=value pairs in the project .env file."""

    env_path = Path(".env")
    existing: Dict[str, str] = {}
    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.rstrip().split("=", 1)
                    existing[k] = v

    # Apply updates
    existing.update({k: str(v) for k, v in updates.items() if v is not None})

    # Write back, preserving order (env keys are few)
    with env_path.open("w", encoding="utf-8") as fh:
        for k, v in existing.items():
            fh.write(f"{k}={v}\n")


@config_app.command("set")
def config_set(
    model: str = typer.Option(None, "--model", help="Default LLM model (LLM_MODEL)."),
    batch_size: int = typer.Option(None, "--batch-size", min=1, help="Default fetch batch size (BATCH_SIZE)."),
):
    """Update defaults in the .env file (model, batch size)."""

    if model is None and batch_size is None:
        typer.echo("Nothing to update. Use --model and/or --batch-size.")
        raise typer.Exit()

    from config import AVAILABLE_MODELS

    updates: Dict[str, str | int] = {}

    if model is not None:
        models_available = {m["model"] for m in AVAILABLE_MODELS}
        if model not in models_available:
            typer.echo(f"Model '{model}' is not in config.AVAILABLE_MODELS")
            raise typer.Exit(code=1)
        updates["LLM_MODEL"] = model

    if batch_size is not None:
        updates["BATCH_SIZE"] = batch_size

    _update_env_file(**updates)
    typer.echo(".env updated successfully. Run 'config show' to verify.")


@app.command("ui")
def ui_command():
    """Open the local HTML editor in your default browser.

    The editor runs entirely locally (no server). For in-place Save back to the
    original JSON file, use a Chromium-based browser (Chrome/Edge) which supports
    the File System Access API. Safari/Firefox can read and export/copy.
    """

    html_path = Path(__file__).resolve().parent / "ui" / "IssueDbEditor.html"
    if not html_path.exists():
        typer.echo(f"Editor UI not found at {html_path}. Please ensure the file exists.")
        raise typer.Exit(code=1)

    typer.echo("Opening Issues DB Editor... Tip: use Chrome/Edge for in-place Save.")
    try:
        webbrowser.open(html_path.as_uri())
    except Exception as exc:  # noqa: WPS429
        typer.echo(f"Failed to open browser: {exc}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    # Running as a module: ``python -m cli``
    # Equivalent to calling ``typer.run`` but retains sub-commands.
    app() 
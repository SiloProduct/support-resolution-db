"""Command-line entrypoint for the Silo Support Ticket Issue Clustering tool."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm

from data_fetcher import fetch_resolved_ticket_ids
from conversation_utils import build_conversation, save_conversation, is_ignored
from issue_clusterer import IssueClusterer


def run(
    pages: int,
    batch_size: int | None,
    output: Path,
    verbose: bool,
    ticket_ids: Optional[List[int]] = None,
    prompt_debug: bool = False,
    reprocess: bool = False,
    refresh: bool = False,
):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    if ticket_ids is None:
        logging.info("Fetching ticket IDs…")
        ticket_ids = fetch_resolved_ticket_ids(pages)
    logging.info("%d tickets to process", len(ticket_ids))

    clusterer = IssueClusterer(load_existing=True, db_path=output)

    from data_fetcher import fetch_ticket  # local import to avoid circular
    from conversation_utils import load_conversation

    for tid in tqdm(ticket_ids, desc="Processing tickets"):
        # Skip if conversation is marked as ignored
        if is_ignored(tid):
            logging.debug("Ticket %d is marked as ignored, skipping", tid)
            continue

        # Skip if ticket already processed and not reprocessing
        if clusterer.has_ticket(tid) and not reprocess:
            logging.debug("Ticket %d already in DB, skipping", tid)
            continue

        conv = None
        if not refresh:
            conv = load_conversation(tid)
        if conv is None or refresh:
            ticket_json = fetch_ticket(tid)
            conv = build_conversation(ticket_json)
            save_conversation(conv)

        clusterer.process_conversation(conv, debug=prompt_debug)

        if not prompt_debug:
            # Persist after each ticket to safeguard against interruptions
            clusterer.save(output)

    if not prompt_debug:
        logging.info("Written consolidated DB to %s", output)
    else:
        logging.info("Prompt debug mode: no DB written")


def main():
    parser = argparse.ArgumentParser(description="Silo Ticket Issue Clustering")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pages", type=int, default=5, help="Pages of ticket IDs to fetch")
    group.add_argument(
        "--ticket-ids",
        type=str,
        help="Comma-separated list of ticket IDs to process manually",
    )

    parser.add_argument("--batch-size", type=int, help="Conversation fetch batch size")
    parser.add_argument(
        "--output", type=Path, default=Path("output/silo_issues_db.json"), help="Output DB path"
    )
    parser.add_argument("--prompt-debug", action="store_true", help="Print prompts/LLM output only")
    parser.add_argument("--reprocess", action="store_true", help="Re-run LLM on existing cached conversations")
    parser.add_argument("--refresh", action="store_true", help="Re-fetch conversations from Freshdesk before processing")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    ids_list = None
    if args.ticket_ids:
        ids_list = [int(x.strip()) for x in args.ticket_ids.split(",") if x.strip()]

    run(
        pages=args.pages,
        batch_size=args.batch_size,
        output=args.output,
        verbose=args.verbose,
        ticket_ids=ids_list,
        prompt_debug=args.prompt_debug,
        reprocess=args.reprocess,
        refresh=args.refresh,
    )


if __name__ == "__main__":
    main() 
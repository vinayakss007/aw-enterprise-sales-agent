"""CLI entry point for background workers.

Usage::

    python -m app.workers campaigns --once          # one tick, then exit
    python -m app.workers campaigns --interval 30   # loop forever (default)
    python -m app.workers campaigns --tenant <uuid> # scope to one tenant
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.db.session import SessionLocal
from app.observability.logging import setup_logging
from app.workers.campaigns import CampaignWorker

logger = logging.getLogger(__name__)


async def _run_campaigns(args: argparse.Namespace) -> int:
    db = SessionLocal()
    try:
        worker = CampaignWorker(db)
        if args.once:
            stats = await worker.process_due_assignments(tenant_id=args.tenant)
            logger.info("campaigns tick (once): %s", stats.as_dict())
            return 0 if not stats.errors else 1
        await worker.run_forever(
            interval_seconds=args.interval, tenant_id=args.tenant
        )
        return 0
    finally:
        db.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.workers")
    sub = parser.add_subparsers(dest="worker", required=True)
    campaigns = sub.add_parser("campaigns", help="Run the campaign execution worker")
    campaigns.add_argument(
        "--once", action="store_true", help="Run a single tick then exit"
    )
    campaigns.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Seconds between ticks when looping (default: 30)",
    )
    campaigns.add_argument(
        "--tenant",
        type=str,
        default=None,
        help="Restrict processing to a single tenant id",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.worker == "campaigns":
        try:
            return asyncio.run(_run_campaigns(args))
        except KeyboardInterrupt:
            return 130
    parser.error(f"unknown worker {args.worker!r}")
    return 2  # unreachable, keeps type checkers happy


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

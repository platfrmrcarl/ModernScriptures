#!/usr/bin/env python3
"""Walk a book's source JSON and produce modernized JSON via local Ollama.

Usage:
  python scripts/modernize.py --book pgp
  python scripts/modernize.py --all
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import ollama

from modern_scriptures.fetcher import BOOKS
from modern_scriptures.walk import modernize_book

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "data" / "source"
DST_DIR = ROOT / "data" / "modernized"
FAILED_LOG = ROOT / "data" / "failed.jsonl"
MODEL = "gemma4:latest"


def _progress_factory(slug: str, total: int):
    state = {"done": 0, "fails": 0, "start": time.time()}

    def progress(verse, result):
        state["done"] += 1
        if not result.ok:
            state["fails"] += 1
        if state["done"] % 25 == 0 or state["done"] == total:
            elapsed = time.time() - state["start"]
            rate = state["done"] / max(1e-6, elapsed)
            print(
                f"[modernize:{slug}] {state['done']}/{total} "
                f"({state['fails']} failed) {rate:.2f} v/s",
                file=sys.stderr,
            )
    return progress


def run_one(slug: str) -> None:
    src = SRC_DIR / f"{slug}.json"
    dst = DST_DIR / f"{slug}.json"
    if not src.exists():
        raise SystemExit(f"missing source: {src}; run fetch_source.py --book {slug} first")
    # Count for progress reporting
    from modern_scriptures.schema import read_book
    total = len(read_book(src))
    client = ollama.Client()
    print(f"[modernize:{slug}] starting; total={total}", file=sys.stderr)
    modernize_book(
        client, src, dst,
        failed_log=FAILED_LOG,
        model=MODEL,
        progress=_progress_factory(slug, total),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--book", choices=list(BOOKS))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    for slug in (list(BOOKS) if args.all else [args.book]):
        run_one(slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

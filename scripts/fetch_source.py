#!/usr/bin/env python3
"""Fetch canonical PD scripture text and write data/source/<slug>.json.

Usage:
  python scripts/fetch_source.py --book pgp
  python scripts/fetch_source.py --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from modern_scriptures.fetcher import BOOKS, normalize_bcbooks, normalize_dc
from modern_scriptures.schema import write_book

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "source"

# Primary source. If it 404s, the script aborts loudly.
URLS = {
    "pgp":    "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/pearl-of-great-price.json",
    "bom":    "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/book-of-mormon.json",
    "dc":     "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/doctrine-and-covenants.json",
    "kjv-ot": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/old-testament.json",
    "kjv-nt": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/new-testament.json",
}


def fetch_one(slug: str) -> None:
    url = URLS[slug]
    print(f"[fetch] {slug}: GET {url}", file=sys.stderr)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    raw = r.json()
    verses = normalize_dc(raw) if slug == "dc" else normalize_bcbooks(raw)
    out_path = DATA_DIR / f"{slug}.json"
    write_book(out_path, verses)
    print(f"[fetch] {slug}: {len(verses)} verses -> {out_path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--book", choices=list(BOOKS))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    slugs = list(BOOKS) if args.all else [args.book]
    for slug in slugs:
        fetch_one(slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

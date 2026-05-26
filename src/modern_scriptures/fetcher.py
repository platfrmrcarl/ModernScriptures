"""Fetch and normalize canonical public-domain scripture text."""

from __future__ import annotations

from .schema import Verse

# Mapping of our internal slug -> upstream identifier.
BOOKS = {
    "pgp":    "pearl-of-great-price",
    "bom":    "book-of-mormon",
    "dc":     "doctrine-and-covenants",
    "kjv-ot": "old-testament",
    "kjv-nt": "new-testament",
}


def normalize_bcbooks(raw: dict) -> list[Verse]:
    """Normalize bcbooks/scriptures-json shape to a flat list of Verse."""
    out: list[Verse] = []
    for book in raw.get("books", []):
        bname = book["book"]
        for ch in book.get("chapters", []):
            cnum = int(ch["chapter"])
            for v in ch.get("verses", []):
                out.append(Verse(
                    book=bname,
                    chapter=cnum,
                    verse=int(v["verse"]),
                    original=v["text"].strip(),
                    modernized=None,
                ))
    return out

"""PDF layout helpers (book/chapter/verse grouping and ReportLab styles)."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch

from .schema import Verse


def group_by_chapter(verses: Iterable[Verse]) -> dict[tuple[str, int], list[Verse]]:
    """Group verses by (book, chapter).

    Books appear in encounter order (preserves canonical source order — e.g.
    Genesis, Exodus, ... — rather than alphabetical). Chapters within a book
    are sorted numerically; verses within a chapter are sorted numerically.
    """
    book_order: list[str] = []
    seen: set[str] = set()
    groups: dict[tuple[str, int], list[Verse]] = defaultdict(list)
    for v in verses:
        if v.book not in seen:
            seen.add(v.book)
            book_order.append(v.book)
        groups[(v.book, v.chapter)].append(v)
    book_index = {b: i for i, b in enumerate(book_order)}
    ordered: dict[tuple[str, int], list[Verse]] = {}
    for key in sorted(groups.keys(), key=lambda k: (book_index[k[0]], k[1])):
        ordered[key] = sorted(groups[key], key=lambda x: x.verse)
    return ordered


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title":   ParagraphStyle("title",   parent=base["Title"],   fontSize=28, leading=34, spaceAfter=0.4 * inch),
        "book":    ParagraphStyle("book",    parent=base["Heading1"], fontSize=20, leading=26, spaceBefore=0.4 * inch, spaceAfter=0.2 * inch),
        "chapter": ParagraphStyle("chapter", parent=base["Heading2"], fontSize=14, leading=18, spaceBefore=0.2 * inch, spaceAfter=0.1 * inch),
        "verse":   ParagraphStyle("verse",   parent=base["BodyText"], fontSize=11, leading=15, spaceAfter=4, firstLineIndent=0),
        "toc":     ParagraphStyle("toc",     parent=base["BodyText"], fontSize=12, leading=16),
    }

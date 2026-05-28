#!/usr/bin/env python3
"""Render modernized verses to a single PDF.

Usage:
  python scripts/render_pdf.py
  python scripts/render_pdf.py --src data/modernized --out ModernScriptures.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.pagesizes import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, PageBreak, Spacer,
)

from modern_scriptures.layout import build_styles, group_by_chapter
from modern_scriptures.schema import read_book
from modern_scriptures.quick_modernize import quick_modernize

# 6x9 inches in points.
PAGE_SIZE = (6 * inch, 9 * inch)

# Order books appear in the output PDF.
BOOK_ORDER = ["kjv-ot", "kjv-nt", "bom", "dc", "pgp"]
BOOK_TITLES = {
    "kjv-ot": "Old Testament",
    "kjv-nt": "New Testament",
    "bom":    "Book of Mormon",
    "dc":     "Doctrine and Covenants",
    "pgp":    "Pearl of Great Price",
}


def _verse_paragraph(v, style):
    # Apply quick_modernize to every verse body — the LLM frequently leaves
    # residual archaic words (unto/verily/thee) in its "modernized" output,
    # so we run the deterministic pass on top regardless of source.
    body = quick_modernize(v.modernized if v.modernized else v.original)
    return Paragraph(f'<font size=8><super>{v.verse}</super></font> {body}', style)


def render(src_dir: Path, out_path: Path, title: str = "Modern Scriptures") -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=PAGE_SIZE,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title=title,
    )

    story = []
    # Title page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(title, styles["title"]))
    story.append(PageBreak())

    # Table of contents (simple — list books that have files)
    story.append(Paragraph("Contents", styles["book"]))
    available = [s for s in BOOK_ORDER if (src_dir / f"{s}.json").exists()]
    for slug in available:
        story.append(Paragraph(BOOK_TITLES[slug], styles["toc"]))
    story.append(PageBreak())

    for slug in available:
        verses = read_book(src_dir / f"{slug}.json")
        if not verses:
            continue
        story.append(Paragraph(BOOK_TITLES[slug], styles["book"]))
        groups = group_by_chapter(verses)
        current_book = None
        for (book, chapter), chapter_verses in groups.items():
            if book != current_book:
                if current_book is not None:
                    story.append(PageBreak())
                story.append(Paragraph(book, styles["book"]))
                current_book = book
            story.append(Paragraph(f"Chapter {chapter}", styles["chapter"]))
            for v in chapter_verses:
                story.append(_verse_paragraph(v, styles["verse"]))
        story.append(PageBreak())

    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="data/modernized")
    parser.add_argument("--out", default="ModernScriptures.pdf")
    parser.add_argument("--title", default="Modern Scriptures")
    args = parser.parse_args()
    render(Path(args.src), Path(args.out), title=args.title)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

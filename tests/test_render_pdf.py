from pathlib import Path

from modern_scriptures.schema import Verse, write_book


def test_render_pdf_produces_nonempty_file(tmp_path: Path):
    from scripts.render_pdf import render
    src = tmp_path / "modernized"
    src.mkdir()
    write_book(src / "pgp.json", [
        Verse("Moses", 1, 1, "o1", "Modernized one."),
        Verse("Moses", 1, 2, "o2", "Modernized two."),
        Verse("Abraham", 1, 1, "o3", "Modernized three."),
    ])
    out = tmp_path / "out.pdf"
    render(src, out, title="Modern Scriptures (Test)")
    assert out.exists() and out.stat().st_size > 1000
    # PDF magic bytes
    assert out.read_bytes()[:4] == b"%PDF"


def test_renderer_uses_quick_modernize_fallback_for_none():
    """When modernized is None, renderer should emit the quick_modernize
    output rather than the raw archaic original wrapped in <i>."""
    from scripts.render_pdf import _verse_paragraph
    from modern_scriptures.layout import build_styles

    styles = build_styles()
    v = Verse("Matthew", 5, 17, "Thou shalt not tempt the Lord thy God.", None)
    para = _verse_paragraph(v, styles["verse"])
    # Paragraph stores its raw text in `.text` (reportlab API).
    text = para.text
    # Modernized words must appear.
    assert "You will not" in text
    assert "your God" in text
    # Archaic words must NOT appear.
    assert "Thou shalt" not in text
    assert "thy God" not in text
    # Must not be italicized (fallback is good enough to be primary text).
    assert "<i>" not in text

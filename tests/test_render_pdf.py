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


def test_renderer_strips_archaic_words_from_llm_modernized_text():
    """The LLM frequently leaves residual archaic words (unto/verily/thee)
    in its 'modernized' output. The renderer must run quick_modernize on
    every verse body so those don't reach the page."""
    from scripts.render_pdf import _verse_paragraph
    from modern_scriptures.layout import build_styles

    styles = build_styles()
    v = Verse(
        "Doctrine and Covenants", 1, 1,
        "Hearken, O ye people of my church, saith the voice of him.",
        "Hearken, O ye people of my church, says the voice of him; "
        "verily I say unto thee.",
    )
    para = _verse_paragraph(v, styles["verse"])
    text = para.text
    assert "ye " not in text and " ye." not in text
    assert "verily" not in text and "Verily" not in text
    assert "unto" not in text and "Unto" not in text
    assert "thee" not in text and "Thee" not in text

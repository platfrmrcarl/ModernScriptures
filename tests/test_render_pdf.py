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

import json
import tempfile
from pathlib import Path

from modern_scriptures.schema import Verse, read_book, write_book


def test_verse_to_dict_roundtrip():
    v = Verse(book="1 Nephi", chapter=1, verse=1, original="orig", modernized=None)
    assert Verse.from_dict(v.to_dict()) == v


def test_write_book_then_read_book():
    verses = [
        Verse(book="Moses", chapter=1, verse=1, original="The words...", modernized=None),
        Verse(book="Moses", chapter=1, verse=2, original="And he saw...", modernized="And he saw..."),
    ]
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "pgp.json"
        write_book(path, verses)
        assert read_book(path) == verses


def test_write_book_is_atomic(tmp_path):
    path = tmp_path / "pgp.json"
    write_book(path, [Verse(book="Moses", chapter=1, verse=1, original="x", modernized=None)])
    # Must not leave a .tmp lying around on success.
    assert not (path.parent / (path.name + ".tmp")).exists()
    assert path.exists()


def test_read_book_missing_file_returns_empty(tmp_path):
    assert read_book(tmp_path / "nope.json") == []

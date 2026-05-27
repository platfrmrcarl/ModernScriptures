from modern_scriptures.layout import group_by_chapter
from modern_scriptures.schema import Verse


def test_group_by_chapter_orders_verses():
    verses = [
        Verse("Moses", 1, 2, "o2", "m2"),
        Verse("Moses", 1, 1, "o1", "m1"),
        Verse("Moses", 2, 1, "o3", "m3"),
    ]
    grouped = group_by_chapter(verses)
    assert list(grouped.keys()) == [("Moses", 1), ("Moses", 2)]
    assert [v.verse for v in grouped[("Moses", 1)]] == [1, 2]
    assert [v.verse for v in grouped[("Moses", 2)]] == [1]


def test_group_by_chapter_preserves_source_book_order():
    """Books must appear in encounter order, not alphabetical.

    Genesis must come before Amos even though A < G alphabetically.
    """
    verses = [
        Verse("Genesis", 1, 1, "g1", "g1"),
        Verse("Exodus", 1, 1, "e1", "e1"),
        Verse("Amos", 1, 1, "a1", "a1"),
        Verse("1 Samuel", 1, 1, "s1", "s1"),
    ]
    grouped = group_by_chapter(verses)
    books_in_order = [book for book, _ in grouped.keys()]
    assert books_in_order == ["Genesis", "Exodus", "Amos", "1 Samuel"]

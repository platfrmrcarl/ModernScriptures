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

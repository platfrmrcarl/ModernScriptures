from modern_scriptures.fetcher import normalize_bcbooks


def test_normalize_bcbooks_pgp_minimal():
    # Simulated minimal structure: one book, one chapter, two verses.
    raw = {
        "books": [
            {
                "book": "Moses",
                "chapters": [
                    {
                        "chapter": 1,
                        "verses": [
                            {"verse": 1, "text": "The words of God, which he spake unto Moses..."},
                            {"verse": 2, "text": "And he saw God face to face..."},
                        ],
                    }
                ],
            }
        ]
    }
    verses = normalize_bcbooks(raw)
    assert len(verses) == 2
    assert verses[0].book == "Moses"
    assert verses[0].chapter == 1
    assert verses[0].verse == 1
    assert verses[0].original.startswith("The words of God")
    assert verses[0].modernized is None

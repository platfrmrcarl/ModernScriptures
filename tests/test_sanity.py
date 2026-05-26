from modern_scriptures.sanity import check_modernization


def test_passes_clean_modernization():
    ok, reason = check_modernization(
        "And it came to pass that Nephi said unto his father:",
        "Nephi said to his father:",
    )
    assert ok, reason


def test_rejects_empty_output():
    ok, reason = check_modernization("And it came to pass", "")
    assert not ok and "length" in reason.lower()


def test_rejects_too_long_output():
    original = "Nephi said."
    runaway = "Nephi said. " * 100
    ok, reason = check_modernization(original, runaway)
    assert not ok and "length" in reason.lower()


def test_rejects_dropped_proper_name():
    ok, reason = check_modernization(
        "And Nephi said unto Lehi: Father, I will go.",
        "He said to his father: I will go.",
    )
    assert not ok and "name" in reason.lower()


def test_rejects_preamble_sure():
    ok, reason = check_modernization("Nephi said.", "Sure, here is the modernization: Nephi said.")
    assert not ok and "preamble" in reason.lower()


def test_rejects_preamble_here_is():
    ok, reason = check_modernization("Nephi said.", "Here is the modernized verse: Nephi said.")
    assert not ok and "preamble" in reason.lower()


def test_rejects_wrapping_quotes():
    ok, reason = check_modernization("Nephi said.", '"Nephi said."')
    assert not ok and "preamble" in reason.lower()


def test_allows_quoted_dialogue_inside():
    ok, reason = check_modernization(
        'And he said: "I will go."', 'He said: "I will go."'
    )
    assert ok, reason

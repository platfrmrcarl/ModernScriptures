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


def test_passes_when_theological_term_lowercased():
    # LLM legitimately lowercases "Gospel" to "gospel" - this should pass.
    ok, reason = check_modernization(
        "to preach the Gospel and administer in the ordinances thereof.",
        "to preach the gospel and administer in the ordinances thereof.",
    )
    assert ok, reason


def test_passes_when_hyphenated_name_loses_hyphen():
    # "Beth-el" -> "Bethel" is a stylistic normalization, not a name drop.
    ok, reason = check_modernization(
        "And he pitched his tent east of Beth-el.",
        "And he pitched his tent east of Bethel.",
    )
    assert ok, reason


def test_still_rejects_genuine_name_drop():
    # "Sarai" -> "Sarah" IS a name change; the gate must still catch it.
    # (Renderer fallback will handle these so they don't appear archaic.)
    ok, reason = check_modernization(
        "But Sarai was barren; she had no child.",
        "But Sarah was barren; she had no child.",
    )
    assert not ok and "name" in reason.lower()


def test_passes_when_sentence_start_verb_rephrased():
    # "Remember that..." -> rephrased to "Without faith you can do nothing..."
    # "Remember" should be in _COMMON_CAPS so it's not flagged as a proper name.
    ok, reason = check_modernization(
        "Remember that without faith you can do nothing; therefore ask in faith.",
        "Without faith you can do nothing, so ask in faith.",
    )
    assert ok, reason


def test_passes_when_jun_abbreviation_modernized():
    # "Joseph Smith, Jun." -> "Joseph Smith Jr." -- "Jun" added to _COMMON_CAPS.
    ok, reason = check_modernization(
        "called upon my servant Joseph Smith, Jun., and spake unto him.",
        "called upon my servant Joseph Smith Jr., and spoke to him.",
    )
    assert ok, reason

from modern_scriptures.prompt import SYSTEM_PROMPT, build_messages


def test_system_prompt_mentions_rules():
    p = SYSTEM_PROMPT.lower()
    assert "thee" in p and "thou" in p
    assert "niv" in p or "esv" in p
    assert "proper name" in p


def test_system_prompt_includes_example():
    assert "EXAMPLE INPUT" in SYSTEM_PROMPT
    assert "EXAMPLE OUTPUT" in SYSTEM_PROMPT


def test_build_messages_shape():
    msgs = build_messages("And it came to pass that Nephi said.")
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == SYSTEM_PROMPT
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "And it came to pass that Nephi said."


def test_build_messages_with_retry_nudge():
    base = build_messages("Verse.")
    nudged = build_messages("Verse.", retry_nudge="Output only the verse.")
    assert nudged[1]["content"].endswith("Output only the verse.")
    assert "Verse." in nudged[1]["content"]
    assert base != nudged

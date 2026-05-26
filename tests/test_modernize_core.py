from unittest.mock import MagicMock

from modern_scriptures.modernize_core import modernize_one


def _client_with_replies(replies):
    fake = MagicMock()
    fake.chat.side_effect = [{"message": {"content": r}} for r in replies]
    return fake


def test_success_first_try():
    client = _client_with_replies(["Nephi said to his father."])
    result = modernize_one(client, "And Nephi said unto his father.", model="gemma4:26b")
    assert result.ok
    assert result.modernized == "Nephi said to his father."
    assert result.attempts == 1


def test_retries_on_preamble_then_succeeds():
    client = _client_with_replies([
        "Here is the modernization: Nephi said.",  # preamble -> fail
        "Nephi said.",  # ok
    ])
    result = modernize_one(client, "Nephi said.", model="gemma4:26b")
    assert result.ok
    assert result.attempts == 2


def test_gives_up_after_3_failures():
    client = _client_with_replies(["", "", ""])  # all length-fail
    result = modernize_one(client, "Some verse text here.", model="gemma4:26b", max_attempts=3)
    assert not result.ok
    assert result.modernized is None
    assert result.attempts == 3
    assert "length" in result.last_reason

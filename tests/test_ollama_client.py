from unittest.mock import MagicMock

from modern_scriptures.ollama_client import modernize_verse


def test_modernize_verse_calls_ollama_with_messages():
    fake = MagicMock()
    fake.chat.return_value = {"message": {"content": "I will go and do."}}
    out = modernize_verse(
        fake,
        "I will go and do the things which the Lord hath commanded.",
        model="gemma4:26b",
    )
    assert out == "I will go and do."
    fake.chat.assert_called_once()
    kwargs = fake.chat.call_args.kwargs or fake.chat.call_args[1]
    assert kwargs["model"] == "gemma4:26b"
    msgs = kwargs["messages"]
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_modernize_verse_strips_whitespace():
    fake = MagicMock()
    fake.chat.return_value = {"message": {"content": "  out  \n"}}
    out = modernize_verse(fake, "in", model="gemma4:26b")
    assert out == "out"


def test_modernize_verse_passes_retry_nudge():
    fake = MagicMock()
    fake.chat.return_value = {"message": {"content": "x"}}
    modernize_verse(fake, "in", model="gemma4:26b", retry_nudge="Try again.")
    kwargs = fake.chat.call_args.kwargs or fake.chat.call_args[1]
    user_msg = kwargs["messages"][1]["content"]
    assert "Try again." in user_msg

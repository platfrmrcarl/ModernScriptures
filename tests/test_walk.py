import json
from pathlib import Path
from unittest.mock import MagicMock

from modern_scriptures.schema import Verse, write_book, read_book
from modern_scriptures.walk import modernize_book


def _client_with_replies(replies):
    fake = MagicMock()
    fake.chat.side_effect = [{"message": {"content": r}} for r in replies]
    return fake


def test_processes_all_verses(tmp_path: Path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    failed = tmp_path / "failed.jsonl"
    write_book(src, [
        Verse("Moses", 1, 1, "The first verse of the scripture text.", None),
        Verse("Moses", 1, 2, "The second verse of the scripture text.", None),
    ])
    client = _client_with_replies([
        "The first verse of scripture.",
        "The second verse of scripture.",
    ])
    modernize_book(client, src, dst, failed_log=failed, model="gemma4:26b")
    out = read_book(dst)
    assert [v.modernized for v in out] == [
        "The first verse of scripture.",
        "The second verse of scripture.",
    ]
    assert not failed.exists() or failed.stat().st_size == 0


def test_skips_already_modernized(tmp_path: Path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    write_book(src, [
        Verse("Moses", 1, 1, "The first verse of the scripture text.", None),
        Verse("Moses", 1, 2, "The second verse of the scripture text.", None),
    ])
    # Pre-populate dst with verse 1 already modernized.
    write_book(dst, [
        Verse("Moses", 1, 1, "The first verse of the scripture text.", "Already modernized here."),
        Verse("Moses", 1, 2, "The second verse of the scripture text.", None),
    ])
    client = _client_with_replies(["The second verse of scripture."])  # Only verse 2 expected
    modernize_book(client, src, dst, failed_log=tmp_path / "failed.jsonl", model="gemma4:26b")
    out = read_book(dst)
    assert out[0].modernized == "Already modernized here."
    assert out[1].modernized == "The second verse of scripture."
    assert client.chat.call_count == 1


def test_logs_failures_and_continues(tmp_path: Path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    failed = tmp_path / "failed.jsonl"
    write_book(src, [
        Verse("Moses", 1, 1, "This tricky verse will fail to modernize properly.", None),
        Verse("Moses", 1, 2, "This easy verse will modernize without any trouble.", None),
    ])
    # 3 empties for verse 1 (all fail length check), then a good reply for verse 2.
    client = _client_with_replies(["", "", "", "This easy verse modernizes without any trouble."])
    modernize_book(client, src, dst, failed_log=failed, model="gemma4:26b")
    out = read_book(dst)
    assert out[0].modernized is None
    assert out[1].modernized == "This easy verse modernizes without any trouble."
    lines = failed.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["book"] == "Moses" and record["chapter"] == 1 and record["verse"] == 1

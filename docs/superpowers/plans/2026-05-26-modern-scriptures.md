# Modern Scriptures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a three-script Python pipeline that fetches public-domain LDS Standard Works text, modernizes each verse via local `gemma4:26b` (Ollama), and renders the result to a single PDF. Pilot on Pearl of Great Price; then run the remaining three books.

**Architecture:** `fetch_source.py → modernize.py → render_pdf.py`, with JSON files as the contract between stages. Shared logic lives in `src/modern_scriptures/` (schema, sanity checks, prompt, Ollama client). Each verse is persisted as it completes so any crash is resumable.

**Tech Stack:** Python 3.11+, `requests` (fetch), `ollama` Python client, `reportlab` (PDF), `pytest` (tests).

---

## File Structure

```
src/modern_scriptures/
  __init__.py
  schema.py           # Verse dataclass + JSON I/O (atomic write)
  sanity.py           # per-verse sanity checks
  prompt.py           # system prompt + few-shot + build_messages()
  ollama_client.py    # thin modernize_verse() wrapper around ollama.chat
  fetcher.py          # source-fetch helpers per book
  layout.py           # ReportLab style/layout helpers
scripts/
  fetch_source.py     # CLI: fetch one or all books → data/source/<book>.json
  modernize.py        # CLI: modernize one or all books → data/modernized/<book>.json
  render_pdf.py       # CLI: render PDF from data/modernized/*.json
tests/
  conftest.py
  test_schema.py
  test_sanity.py
  test_prompt.py
  test_ollama_client.py
  test_fetcher.py
  test_modernize.py
  test_layout.py
  test_render_pdf.py
data/
  source/             # gitignored
  modernized/         # gitignored
requirements.txt
pyproject.toml
```

Each file in `src/modern_scriptures/` is small and has one job. Scripts in `scripts/` are thin CLI wrappers.

---

## Task 1: Project scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `src/modern_scriptures/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write a smoke test**

Create `tests/test_smoke.py`:

```python
def test_package_imports():
    import modern_scriptures  # noqa: F401
```

- [ ] **Step 2: Run it to confirm it fails**

```bash
cd /home/carl/GitHub/ModernScriptures
python -m pytest tests/test_smoke.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'modern_scriptures'`.

- [ ] **Step 3: Create scaffolding files**

`requirements.txt`:

```
requests==2.32.3
ollama==0.4.4
reportlab==4.2.5
pytest==8.3.3
```

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "modern_scriptures"
version = "0.1.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

`src/modern_scriptures/__init__.py`:

```python
"""Modern Scriptures pipeline package."""
```

`tests/conftest.py`:

```python
# Empty for now; future fixtures live here.
```

- [ ] **Step 4: Set up venv, install deps, re-run smoke test**

```bash
cd /home/carl/GitHub/ModernScriptures
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/pytest tests/test_smoke.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pyproject.toml src/ tests/
git commit -m "chore: project scaffolding (pyproject, deps, smoke test)"
```

---

## Task 2: Verse schema and JSON I/O

**Files:**
- Create: `src/modern_scriptures/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write failing tests**

`tests/test_schema.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_schema.py -v
```

Expected: ModuleNotFoundError on `modern_scriptures.schema`.

- [ ] **Step 3: Implement**

`src/modern_scriptures/schema.py`:

```python
"""Verse data model and JSON I/O."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Verse:
    book: str
    chapter: int
    verse: int
    original: str
    modernized: str | None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Verse":
        return cls(
            book=d["book"],
            chapter=int(d["chapter"]),
            verse=int(d["verse"]),
            original=d["original"],
            modernized=d.get("modernized"),
        )


def read_book(path: Path) -> list[Verse]:
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Verse.from_dict(d) for d in data]


def write_book(path: Path, verses: list[Verse]) -> None:
    """Atomic write: write to .tmp then os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump([v.to_dict() for v in verses], f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_schema.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/schema.py tests/test_schema.py
git commit -m "feat: Verse dataclass and atomic JSON I/O"
```

---

## Task 3: Sanity checks

**Files:**
- Create: `src/modern_scriptures/sanity.py`
- Create: `tests/test_sanity.py`

- [ ] **Step 1: Write failing tests**

`tests/test_sanity.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_sanity.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/sanity.py`:

```python
"""Per-verse sanity checks for modernizer output."""

from __future__ import annotations

import re

_PREAMBLE_PREFIXES = (
    "sure,", "sure ", "here is", "here's", "the verse", "the modernized",
    "modernized:", "output:", "translation:",
)

_PROPER_NAME_RE = re.compile(r"\b[A-Z][a-zA-Z'-]{2,}\b")

# Words that look like proper names but are common sentence-starters.
_COMMON_CAPS = {
    "And", "But", "For", "The", "Then", "When", "Where", "Behold", "Yea",
    "Wherefore", "Therefore", "Now", "Also", "Verily", "If", "Of", "In",
    "Lord", "God", "Father", "Son", "Spirit", "Christ", "Jesus", "Holy",
}


def _proper_names(text: str) -> set[str]:
    return {m for m in _PROPER_NAME_RE.findall(text) if m not in _COMMON_CAPS}


def _length_ok(original: str, output: str) -> bool:
    in_len = max(1, len(original))
    out_len = len(output)
    ratio = out_len / in_len
    return 0.4 <= ratio <= 2.5


def _starts_with_preamble(output: str) -> bool:
    lower = output.lstrip().lower()
    if any(lower.startswith(p) for p in _PREAMBLE_PREFIXES):
        return True
    # Wrapping quotes around the entire output.
    stripped = output.strip()
    if len(stripped) >= 2 and stripped[0] in '"“' and stripped[-1] in '"”':
        return True
    return False


def check_modernization(original: str, output: str) -> tuple[bool, str]:
    """Return (passed, reason). reason is "" on pass, else a short label."""
    if not _length_ok(original, output):
        return False, f"length out of bounds ({len(output)} vs {len(original)})"
    if _starts_with_preamble(output):
        return False, "preamble or wrapping quotes detected"
    missing = _proper_names(original) - _proper_names(output)
    if missing:
        return False, f"proper name(s) missing: {sorted(missing)}"
    return True, ""
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_sanity.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/sanity.py tests/test_sanity.py
git commit -m "feat: per-verse sanity checks"
```

---

## Task 4: Prompt construction

**Files:**
- Create: `src/modern_scriptures/prompt.py`
- Create: `tests/test_prompt.py`

- [ ] **Step 1: Write failing tests**

`tests/test_prompt.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_prompt.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/prompt.py`:

```python
"""System prompt and message builder for the modernizer."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are modernizing archaic English scripture into clear contemporary English \
in the style of the NIV or ESV. Rules:
- Replace thee/thou/thy/thine/ye and -eth/-est verb endings.
- Replace archaic vocabulary (e.g. "wherefore" -> "therefore",
  "whence" -> "from where", "hither" -> "here").
- Keep proper names exactly as written. Do not drop any name.
- Preserve theological terms when they have no plain equivalent
  (covenant, iniquity, atonement, etc.).
- Preserve sentence boundaries and meaning faithfully. Do NOT paraphrase.
- Do not add or remove content. Do not explain. Do not add quotation marks
  around the whole output.
- Output ONLY the modernized verse text. No preamble. No labels. No commentary.

EXAMPLE INPUT:
And it came to pass that I, Nephi, said unto my father: I will go and do \
the things which the Lord hath commanded.

EXAMPLE OUTPUT:
I, Nephi, said to my father: I will go and do the things the Lord has commanded.
"""


def build_messages(verse_text: str, retry_nudge: str | None = None) -> list[dict]:
    """Return Ollama-compatible messages for modernizing a single verse."""
    user = verse_text if not retry_nudge else f"{verse_text}\n\n{retry_nudge}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_prompt.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/prompt.py tests/test_prompt.py
git commit -m "feat: modernizer system prompt and message builder"
```

---

## Task 5: Ollama client wrapper

**Files:**
- Create: `src/modern_scriptures/ollama_client.py`
- Create: `tests/test_ollama_client.py`

- [ ] **Step 1: Write failing tests**

`tests/test_ollama_client.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_ollama_client.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/ollama_client.py`:

```python
"""Thin Ollama wrapper used by the modernizer."""

from __future__ import annotations

from .prompt import build_messages


def modernize_verse(
    client,
    verse_text: str,
    *,
    model: str,
    retry_nudge: str | None = None,
    temperature: float = 0.2,
) -> str:
    """Call ollama.chat once for a single verse; return stripped content."""
    response = client.chat(
        model=model,
        messages=build_messages(verse_text, retry_nudge=retry_nudge),
        options={"temperature": temperature},
    )
    return response["message"]["content"].strip()
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_ollama_client.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/ollama_client.py tests/test_ollama_client.py
git commit -m "feat: thin ollama client wrapper for modernize_verse"
```

---

## Task 6: Modernize-one-verse orchestrator (retry + sanity)

**Files:**
- Create: `src/modern_scriptures/modernize_core.py`
- Create: `tests/test_modernize_core.py`

- [ ] **Step 1: Write failing tests**

`tests/test_modernize_core.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_modernize_core.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/modernize_core.py`:

```python
"""Orchestrates: call Ollama, sanity-check, retry up to N times."""

from __future__ import annotations

from dataclasses import dataclass

from .ollama_client import modernize_verse
from .sanity import check_modernization


@dataclass
class ModernizeResult:
    ok: bool
    modernized: str | None
    attempts: int
    last_reason: str


_RETRY_NUDGES = [
    None,
    "Reminder: output only the modernized verse text. No preamble.",
    "Reminder: keep every proper name. Output only the verse text, nothing else.",
]


def modernize_one(client, original: str, *, model: str, max_attempts: int = 3) -> ModernizeResult:
    last_reason = ""
    for attempt in range(1, max_attempts + 1):
        nudge = _RETRY_NUDGES[min(attempt - 1, len(_RETRY_NUDGES) - 1)]
        candidate = modernize_verse(client, original, model=model, retry_nudge=nudge)
        ok, reason = check_modernization(original, candidate)
        if ok:
            return ModernizeResult(ok=True, modernized=candidate, attempts=attempt, last_reason="")
        last_reason = reason
    return ModernizeResult(ok=False, modernized=None, attempts=max_attempts, last_reason=last_reason)
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_modernize_core.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/modernize_core.py tests/test_modernize_core.py
git commit -m "feat: modernize_one orchestrator with retry and sanity check"
```

---

## Task 7: Walk-a-book modernizer (resumable, writes after each verse)

**Files:**
- Create: `src/modern_scriptures/walk.py`
- Create: `tests/test_walk.py`

- [ ] **Step 1: Write failing tests**

`tests/test_walk.py`:

```python
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
        Verse("Moses", 1, 1, "Original one.", None),
        Verse("Moses", 1, 2, "Original two.", None),
    ])
    client = _client_with_replies(["One.", "Two."])
    modernize_book(client, src, dst, failed_log=failed, model="gemma4:26b")
    out = read_book(dst)
    assert [v.modernized for v in out] == ["One.", "Two."]
    assert not failed.exists() or failed.stat().st_size == 0


def test_skips_already_modernized(tmp_path: Path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    write_book(src, [
        Verse("Moses", 1, 1, "Original one.", None),
        Verse("Moses", 1, 2, "Original two.", None),
    ])
    # Pre-populate dst with verse 1 already modernized.
    write_book(dst, [
        Verse("Moses", 1, 1, "Original one.", "Already done."),
        Verse("Moses", 1, 2, "Original two.", None),
    ])
    client = _client_with_replies(["Two."])  # Only verse 2 expected
    modernize_book(client, src, dst, failed_log=tmp_path / "failed.jsonl", model="gemma4:26b")
    out = read_book(dst)
    assert out[0].modernized == "Already done."
    assert out[1].modernized == "Two."
    assert client.chat.call_count == 1


def test_logs_failures_and_continues(tmp_path: Path):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    failed = tmp_path / "failed.jsonl"
    write_book(src, [
        Verse("Moses", 1, 1, "Tricky verse.", None),
        Verse("Moses", 1, 2, "Easy verse.", None),
    ])
    # 3 empties for verse 1 (all fail length), then "Done." for verse 2.
    client = _client_with_replies(["", "", "", "Done."])
    modernize_book(client, src, dst, failed_log=failed, model="gemma4:26b")
    out = read_book(dst)
    assert out[0].modernized is None
    assert out[1].modernized == "Done."
    lines = failed.read_text().strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["book"] == "Moses" and record["chapter"] == 1 and record["verse"] == 1
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_walk.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/walk.py`:

```python
"""Walk a book of verses, modernize each, persist after every verse."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from .modernize_core import modernize_one
from .schema import Verse, read_book, write_book


def modernize_book(
    client,
    src_path: Path,
    dst_path: Path,
    *,
    failed_log: Path,
    model: str,
    progress=None,
) -> None:
    """Modernize every verse in src_path; write to dst_path after each verse.

    Idempotent: any verse in dst_path with a non-null `modernized` is skipped.
    Failures (after retries) are appended to `failed_log` as JSONL and left
    with modernized=None.
    """
    source = read_book(src_path)
    existing = {(v.book, v.chapter, v.verse): v for v in read_book(dst_path)}
    out: list[Verse] = []

    for src_verse in source:
        key = (src_verse.book, src_verse.chapter, src_verse.verse)
        prior = existing.get(key)
        if prior is not None and prior.modernized:
            out.append(prior)
            continue

        result = modernize_one(client, src_verse.original, model=model)
        new_verse = replace(src_verse, modernized=result.modernized)
        out.append(new_verse)
        write_book(dst_path, out + [v for v in source[len(out):] if (v.book, v.chapter, v.verse) not in {(o.book, o.chapter, o.verse) for o in out}])

        if not result.ok:
            failed_log.parent.mkdir(parents=True, exist_ok=True)
            with open(failed_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "book": src_verse.book,
                    "chapter": src_verse.chapter,
                    "verse": src_verse.verse,
                    "reason": result.last_reason,
                }) + "\n")

        if progress is not None:
            progress(src_verse, result)
```

Note: the `write_book` line above writes the partially-modernized list each
iteration. It rebuilds the full book by concatenating (a) the verses processed
so far with (b) the source verses not yet touched.

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_walk.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/walk.py tests/test_walk.py
git commit -m "feat: resumable per-verse book walker with failure logging"
```

---

## Task 8: Source-fetch — Pearl of Great Price (pilot)

**Files:**
- Create: `src/modern_scriptures/fetcher.py`
- Create: `tests/test_fetcher.py`

> **Source choice:** `bcbooks/scriptures-json` on GitHub (raw JSON, MIT-licensed wrapper around public-domain LDS text). If unavailable at runtime, fall back to `beandog/lds-scriptures` (SQLite) or a similar mirror. Implementer: verify URL liveness before running; if both are dead, ask the user to point at a local source.

- [ ] **Step 1: Write failing test**

`tests/test_fetcher.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_fetcher.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/fetcher.py`:

```python
"""Fetch and normalize canonical public-domain scripture text."""

from __future__ import annotations

from .schema import Verse

# Mapping of our internal slug -> upstream identifier.
BOOKS = {
    "pgp": "pearl-of-great-price",
    "bom": "book-of-mormon",
    "dc":  "doctrine-and-covenants",
    "kjv-ot": "old-testament",
    "kjv-nt": "new-testament",
}


def normalize_bcbooks(raw: dict) -> list[Verse]:
    """Normalize bcbooks/scriptures-json shape to a flat list of Verse."""
    out: list[Verse] = []
    for book in raw.get("books", []):
        bname = book["book"]
        for ch in book.get("chapters", []):
            cnum = int(ch["chapter"])
            for v in ch.get("verses", []):
                out.append(Verse(
                    book=bname,
                    chapter=cnum,
                    verse=int(v["verse"]),
                    original=v["text"].strip(),
                    modernized=None,
                ))
    return out
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_fetcher.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/fetcher.py tests/test_fetcher.py
git commit -m "feat: fetcher normalize_bcbooks for canonical scripture JSON"
```

---

## Task 9: `fetch_source.py` CLI

**Files:**
- Create: `scripts/fetch_source.py`

- [ ] **Step 1: Implement the CLI**

`scripts/fetch_source.py`:

```python
#!/usr/bin/env python3
"""Fetch canonical PD scripture text and write data/source/<slug>.json.

Usage:
  python scripts/fetch_source.py --book pgp
  python scripts/fetch_source.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

from modern_scriptures.fetcher import BOOKS, normalize_bcbooks
from modern_scriptures.schema import write_book

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "source"

# Primary source. If it 404s, the script aborts loudly.
URLS = {
    "pgp":    "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/pearl-of-great-price.json",
    "bom":    "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/book-of-mormon.json",
    "dc":     "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/doctrine-and-covenants.json",
    "kjv-ot": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/old-testament.json",
    "kjv-nt": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/new-testament.json",
}


def fetch_one(slug: str) -> None:
    url = URLS[slug]
    print(f"[fetch] {slug}: GET {url}", file=sys.stderr)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    raw = r.json()
    verses = normalize_bcbooks(raw)
    out_path = DATA_DIR / f"{slug}.json"
    write_book(out_path, verses)
    print(f"[fetch] {slug}: {len(verses)} verses -> {out_path}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--book", choices=list(BOOKS))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()

    slugs = list(BOOKS) if args.all else [args.book]
    for slug in slugs:
        fetch_one(slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Smoke-test fetch on PoGP**

```bash
.venv/bin/python scripts/fetch_source.py --book pgp
ls -lh data/source/
.venv/bin/python -c "from modern_scriptures.schema import read_book; from pathlib import Path; vs = read_book(Path('data/source/pgp.json')); print(len(vs), 'verses'); print(vs[0])"
```

Expected: ~600+ verses, first verse from Moses chapter 1.

If the URL 404s: try the alternate source `https://raw.githubusercontent.com/beandog/lds-scriptures/master/json/lds-scriptures.json` (different shape — would require an alternate normalize function). Stop and report which source worked.

- [ ] **Step 3: Sanity-check against the PDF**

Open the PDF to Moses 1:1 (Pearl of Great Price) and confirm the text in `data/source/pgp.json` matches verbatim. If it diverges meaningfully (more than whitespace/punctuation), report what differs.

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch_source.py
git commit -m "feat: fetch_source.py CLI"
```

---

## Task 10: `modernize.py` CLI

**Files:**
- Create: `scripts/modernize.py`

- [ ] **Step 1: Implement the CLI**

`scripts/modernize.py`:

```python
#!/usr/bin/env python3
"""Walk a book's source JSON and produce modernized JSON via local Ollama.

Usage:
  python scripts/modernize.py --book pgp
  python scripts/modernize.py --all
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import ollama

from modern_scriptures.fetcher import BOOKS
from modern_scriptures.walk import modernize_book

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "data" / "source"
DST_DIR = ROOT / "data" / "modernized"
FAILED_LOG = ROOT / "data" / "failed.jsonl"
MODEL = "gemma4:26b"


def _progress_factory(slug: str, total: int):
    state = {"done": 0, "fails": 0, "start": time.time()}

    def progress(verse, result):
        state["done"] += 1
        if not result.ok:
            state["fails"] += 1
        if state["done"] % 25 == 0 or state["done"] == total:
            elapsed = time.time() - state["start"]
            rate = state["done"] / max(1e-6, elapsed)
            print(
                f"[modernize:{slug}] {state['done']}/{total} "
                f"({state['fails']} failed) {rate:.2f} v/s",
                file=sys.stderr,
            )
    return progress


def run_one(slug: str) -> None:
    src = SRC_DIR / f"{slug}.json"
    dst = DST_DIR / f"{slug}.json"
    if not src.exists():
        raise SystemExit(f"missing source: {src}; run fetch_source.py --book {slug} first")
    # Count for progress reporting
    from modern_scriptures.schema import read_book
    total = len(read_book(src))
    client = ollama.Client()
    print(f"[modernize:{slug}] starting; total={total}", file=sys.stderr)
    modernize_book(
        client, src, dst,
        failed_log=FAILED_LOG,
        model=MODEL,
        progress=_progress_factory(slug, total),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--book", choices=list(BOOKS))
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    for slug in (list(BOOKS) if args.all else [args.book]):
        run_one(slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Tiny smoke test (3 verses)**

Before the full pilot, prove the loop works on a tiny slice:

```bash
.venv/bin/python -c "
from pathlib import Path
from modern_scriptures.schema import read_book, write_book
vs = read_book(Path('data/source/pgp.json'))[:3]
write_book(Path('data/source/pgp-tiny.json'), vs)
print('wrote 3 verses')
"
# Temporarily rename for the smoke test:
cp data/source/pgp.json data/source/pgp.json.bak
cp data/source/pgp-tiny.json data/source/pgp.json
.venv/bin/python scripts/modernize.py --book pgp
.venv/bin/python -c "
from pathlib import Path
from modern_scriptures.schema import read_book
for v in read_book(Path('data/modernized/pgp.json')):
    print(f'--- {v.book} {v.chapter}:{v.verse} ---')
    print('OLD:', v.original)
    print('NEW:', v.modernized)
"
# Restore
mv data/source/pgp.json.bak data/source/pgp.json
rm -f data/modernized/pgp.json data/source/pgp-tiny.json
```

Expected: 3 verses modernized with plausible NIV-style output. If any look wrong, stop and tune the prompt before continuing.

- [ ] **Step 3: Commit**

```bash
git add scripts/modernize.py
git commit -m "feat: modernize.py CLI"
```

---

## Task 11: PDF layout helpers

**Files:**
- Create: `src/modern_scriptures/layout.py`
- Create: `tests/test_layout.py`

- [ ] **Step 1: Write failing tests**

`tests/test_layout.py`:

```python
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
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_layout.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement**

`src/modern_scriptures/layout.py`:

```python
"""PDF layout helpers (book/chapter/verse grouping and ReportLab styles)."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch

from .schema import Verse


def group_by_chapter(verses: Iterable[Verse]) -> dict[tuple[str, int], list[Verse]]:
    groups: dict[tuple[str, int], list[Verse]] = defaultdict(list)
    for v in verses:
        groups[(v.book, v.chapter)].append(v)
    # Sort verses inside each chapter and produce a stably-ordered dict.
    ordered: dict[tuple[str, int], list[Verse]] = {}
    for key in sorted(groups.keys()):
        ordered[key] = sorted(groups[key], key=lambda x: x.verse)
    return ordered


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title":   ParagraphStyle("title",   parent=base["Title"],   fontSize=28, leading=34, spaceAfter=0.4 * inch),
        "book":    ParagraphStyle("book",    parent=base["Heading1"], fontSize=20, leading=26, spaceBefore=0.4 * inch, spaceAfter=0.2 * inch),
        "chapter": ParagraphStyle("chapter", parent=base["Heading2"], fontSize=14, leading=18, spaceBefore=0.2 * inch, spaceAfter=0.1 * inch),
        "verse":   ParagraphStyle("verse",   parent=base["BodyText"], fontSize=11, leading=15, spaceAfter=4, firstLineIndent=0),
        "toc":     ParagraphStyle("toc",     parent=base["BodyText"], fontSize=12, leading=16),
    }
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_layout.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add src/modern_scriptures/layout.py tests/test_layout.py
git commit -m "feat: PDF layout helpers (grouping + styles)"
```

---

## Task 12: `render_pdf.py` CLI

**Files:**
- Create: `scripts/render_pdf.py`
- Create: `tests/test_render_pdf.py`

- [ ] **Step 1: Write failing test**

`tests/test_render_pdf.py`:

```python
from pathlib import Path

from modern_scriptures.schema import Verse, write_book


def test_render_pdf_produces_nonempty_file(tmp_path: Path):
    from scripts.render_pdf import render
    src = tmp_path / "modernized"
    src.mkdir()
    write_book(src / "pgp.json", [
        Verse("Moses", 1, 1, "o1", "Modernized one."),
        Verse("Moses", 1, 2, "o2", "Modernized two."),
        Verse("Abraham", 1, 1, "o3", "Modernized three."),
    ])
    out = tmp_path / "out.pdf"
    render(src, out, title="Modern Scriptures (Test)")
    assert out.exists() and out.stat().st_size > 1000
    # PDF magic bytes
    assert out.read_bytes()[:4] == b"%PDF"
```

- [ ] **Step 2: Run, expect failure**

```bash
.venv/bin/pytest tests/test_render_pdf.py -v
```

Expected: ImportError on `scripts.render_pdf`.

- [ ] **Step 3: Implement**

`scripts/render_pdf.py`:

```python
#!/usr/bin/env python3
"""Render modernized verses to a single PDF.

Usage:
  python scripts/render_pdf.py
  python scripts/render_pdf.py --src data/modernized --out ModernScriptures.pdf
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.pagesizes import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, PageBreak, Spacer,
)

from modern_scriptures.layout import build_styles, group_by_chapter
from modern_scriptures.schema import read_book

# 6x9 inches in points.
PAGE_SIZE = (6 * inch, 9 * inch)

# Order books appear in the output PDF.
BOOK_ORDER = ["kjv-ot", "kjv-nt", "bom", "dc", "pgp"]
BOOK_TITLES = {
    "kjv-ot": "Old Testament",
    "kjv-nt": "New Testament",
    "bom":    "Book of Mormon",
    "dc":     "Doctrine and Covenants",
    "pgp":    "Pearl of Great Price",
}


def _verse_paragraph(v, style):
    body = v.modernized if v.modernized else f"[verse {v.chapter}:{v.verse} not yet modernized]"
    return Paragraph(f'<font size=8><super>{v.verse}</super></font> {body}', style)


def render(src_dir: Path, out_path: Path, title: str = "Modern Scriptures") -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=PAGE_SIZE,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title=title,
    )

    story = []
    # Title page
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph(title, styles["title"]))
    story.append(PageBreak())

    # Table of contents (simple — list books that have files)
    story.append(Paragraph("Contents", styles["book"]))
    available = [s for s in BOOK_ORDER if (src_dir / f"{s}.json").exists()]
    for slug in available:
        story.append(Paragraph(BOOK_TITLES[slug], styles["toc"]))
    story.append(PageBreak())

    for slug in available:
        verses = read_book(src_dir / f"{slug}.json")
        if not verses:
            continue
        story.append(Paragraph(BOOK_TITLES[slug], styles["book"]))
        groups = group_by_chapter(verses)
        current_book = None
        for (book, chapter), chapter_verses in groups.items():
            if book != current_book:
                if current_book is not None:
                    story.append(PageBreak())
                story.append(Paragraph(book, styles["book"]))
                current_book = book
            story.append(Paragraph(f"Chapter {chapter}", styles["chapter"]))
            for v in chapter_verses:
                story.append(_verse_paragraph(v, styles["verse"]))
        story.append(PageBreak())

    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="data/modernized")
    parser.add_argument("--out", default="ModernScriptures.pdf")
    parser.add_argument("--title", default="Modern Scriptures")
    args = parser.parse_args()
    render(Path(args.src), Path(args.out), title=args.title)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Also add `scripts/__init__.py` (empty) so the test can `from scripts.render_pdf import render`.

```bash
touch scripts/__init__.py
```

And add `scripts` to `pyproject.toml` pythonpath so the test imports work:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src", "."]
```

- [ ] **Step 4: Run tests, expect pass**

```bash
.venv/bin/pytest tests/test_render_pdf.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render_pdf.py scripts/__init__.py tests/test_render_pdf.py pyproject.toml
git commit -m "feat: render_pdf.py CLI with title/ToC/book/chapter layout"
```

---

## Task 13: Pilot run — Pearl of Great Price end-to-end

This task is a **manual checkpoint**. Do not proceed past it without user sign-off.

- [ ] **Step 1: Ensure Ollama is running and gemma4:26b is loaded**

```bash
ollama list | grep gemma4:26b
# If not listed, pull it:
# ollama pull gemma4:26b
ollama ps  # confirms the daemon is alive
```

- [ ] **Step 2: Fetch PoGP source**

```bash
.venv/bin/python scripts/fetch_source.py --book pgp
wc -l data/source/pgp.json
```

Expected: file written, ~600+ verses.

- [ ] **Step 3: Modernize PoGP (full book)**

This is the long-running step. Expect 30–90 minutes for PoGP at ~10–30 tok/s on consumer GPU.

```bash
.venv/bin/python scripts/modernize.py --book pgp
```

Watch the progress output. If failure rate exceeds ~5%, stop and tune the prompt or sanity checks before continuing.

- [ ] **Step 4: Render pilot PDF**

```bash
.venv/bin/python scripts/render_pdf.py --src data/modernized --out PilotPGP.pdf
```

- [ ] **Step 5: Manual review checkpoint**

Open `PilotPGP.pdf`. Spot-check at least:
- Moses 1:1–5 (opening of Moses)
- Abraham 3:22–28 (a doctrinally weighty passage)
- Joseph Smith—History 1:15–20 (modern English already; should change least)
- 10 random verses

Also review `data/failed.jsonl` (if it exists) for systemic failure patterns.

**Stop here and report findings to the user. Do not proceed to the full run without explicit approval.**

---

## Task 14: Full run — remaining three books

Once the user approves the pilot.

- [ ] **Step 1: Fetch remaining books**

```bash
.venv/bin/python scripts/fetch_source.py --book bom
.venv/bin/python scripts/fetch_source.py --book dc
.venv/bin/python scripts/fetch_source.py --book kjv-ot
.venv/bin/python scripts/fetch_source.py --book kjv-nt
```

- [ ] **Step 2: Modernize each book**

These can be kicked off in background. Total expected runtime: ~15–30 hours.

```bash
.venv/bin/python scripts/modernize.py --book bom    # ~6,500 verses
.venv/bin/python scripts/modernize.py --book dc     # ~3,700 verses
.venv/bin/python scripts/modernize.py --book kjv-nt # ~7,950 verses
.venv/bin/python scripts/modernize.py --book kjv-ot # ~23,000 verses
```

Run sequentially (Ollama can only run one large model at a time on a single GPU). If the machine restarts, just re-run the same commands — they pick up where they left off.

- [ ] **Step 3: Render the final combined PDF**

```bash
.venv/bin/python scripts/render_pdf.py --out ModernScriptures.pdf
```

- [ ] **Step 4: Final review**

Spot-check 20 random verses across the four books. Open the PDF, scroll through, confirm formatting. Review `data/failed.jsonl` for any verses that didn't make it; decide whether to re-run those manually.

- [ ] **Step 5: Final commit**

```bash
# Don't commit the PDF or data/ — they're gitignored.
# Commit any prompt/sanity tweaks you made during the pilot.
git status
git log --oneline | head -20
```

---

## Self-review

**Spec coverage:** ✓ All four books in scope (Tasks 13–14). ✓ NIV/ESV-style prompt (Task 4). ✓ Verse-only content (no headings in render — Task 12). ✓ Pilot on PoGP first (Task 13). ✓ gemma4:26b via Ollama (Task 10). ✓ Canonical PD text source (Tasks 8–9). ✓ Three-script architecture (Tasks 9, 10, 12). ✓ JSON contract between stages (Task 2). ✓ Resumable writes (Task 7). ✓ Sanity + retry + failure log (Tasks 3, 6, 7). ✓ 6×9 single-column PDF with ToC (Task 12).

**Placeholder scan:** No TBDs. Each step shows actual code. Each command shows expected output.

**Type consistency:** `Verse` dataclass field names (`book`, `chapter`, `verse`, `original`, `modernized`) match across schema.py, fetcher.py, walk.py, layout.py, render_pdf.py. `modernize_one` returns `ModernizeResult` with fields used in walk.py. Source slugs (`pgp`, `bom`, `dc`, `kjv-ot`, `kjv-nt`) are consistent in `BOOKS`, `URLS`, `BOOK_ORDER`, and CLI args.

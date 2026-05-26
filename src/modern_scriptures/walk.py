"""Walk a book of verses, modernize each, persist after every verse."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from .modernize_core import ModernizeResult, modernize_one
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

    # Build initial state by overlaying existing modernizations onto source.
    state: list[Verse] = []
    for src_v in source:
        key = (src_v.book, src_v.chapter, src_v.verse)
        prior = existing.get(key)
        if prior is not None and prior.modernized:
            state.append(prior)
        else:
            state.append(src_v)

    for i, src_v in enumerate(source):
        if state[i].modernized:
            continue
        try:
            result = modernize_one(client, src_v.original, model=model)
        except Exception as exc:
            reason = f"exception: {type(exc).__name__}: {exc}"
            state[i] = replace(src_v, modernized=None)
            write_book(dst_path, state)
            failed_log.parent.mkdir(parents=True, exist_ok=True)
            with open(failed_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "book": src_v.book,
                    "chapter": src_v.chapter,
                    "verse": src_v.verse,
                    "reason": reason,
                }) + "\n")
            if progress is not None:
                progress(src_v, ModernizeResult(ok=False, modernized=None, attempts=1, last_reason=reason))
            continue
        state[i] = replace(src_v, modernized=result.modernized)
        write_book(dst_path, state)
        if not result.ok:
            failed_log.parent.mkdir(parents=True, exist_ok=True)
            with open(failed_log, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "book": src_v.book,
                    "chapter": src_v.chapter,
                    "verse": src_v.verse,
                    "reason": result.last_reason,
                }) + "\n")
        if progress is not None:
            progress(src_v, result)

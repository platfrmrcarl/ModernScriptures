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

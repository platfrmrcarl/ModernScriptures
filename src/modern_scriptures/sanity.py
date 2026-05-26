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
    if _starts_with_preamble(output):
        return False, "preamble or wrapping quotes detected"
    if not _length_ok(original, output):
        return False, f"length out of bounds ({len(output)} vs {len(original)})"
    missing = _proper_names(original) - _proper_names(output)
    if missing:
        return False, f"proper name(s) missing: {sorted(missing)}"
    return True, ""

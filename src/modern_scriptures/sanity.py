"""Per-verse sanity checks for modernizer output."""

from __future__ import annotations

import re

_PREAMBLE_PREFIXES = (
    "sure,", "sure ", "here is", "here's", "the verse", "the modernized",
    "modernized:", "output:", "translation:",
)

_PROPER_NAME_RE = re.compile(r"\b[A-Z][a-zA-Z'-]{2,}\b")

# Words that look like proper names but are common sentence-starters.
# Stored lowercase; matched case-insensitively.
_COMMON_CAPS = {w.lower() for w in {
    "And", "But", "For", "The", "Then", "When", "Where", "Behold", "Yea",
    "Wherefore", "Therefore", "Now", "Also", "Verily", "If", "Of", "In",
    "Lord", "God", "Father", "Son", "Spirit", "Christ", "Jesus", "Holy",
    "Thou", "Thee", "Thy", "Thine", "Hast", "Hath", "Doth",
    "Shalt", "Wilt", "Saith", "Cometh", "Goeth", "Knoweth", "Doeth",
    "Unto", "Howbeit", "Thus", "Whosoever", "Whatsoever", "Wherein",
    "Whereby", "Whence", "Hither", "Thither", "That", "This", "These",
    "Those", "Which", "Who",
    "So", "Yet", "Even", "Nevertheless", "Notwithstanding",
    # Pronouns capitalized at sentence start.
    "He", "She", "It", "They", "We", "You", "I", "Me", "Us", "Them", "Mine",
    "Yours", "Hers", "His", "Theirs", "Ours", "One",
    # KJV/scripture-style sentence-start imperatives and archaic verbs/adverbs.
    "Get", "Say", "Know", "Neither", "Fulfil", "Shared", "Take", "Give",
    "See", "Hear", "Come", "Go", "Tell", "Stand", "Speak", "Pass", "Make",
    "Let", "Cast", "Bring", "Put", "Smite", "Eat", "Drink",
    "Art", "Suppose", "Whither", "Suffer", "Except", "Touch", "Believing",
    "Knowest", "Believest", "Sayest", "Doest", "Mayst", "Canst",
    # KJV all-caps for divine names — modernizer correctly outputs title case.
    "LORD", "JEHOVAH", "ZION", "GOD",
}}


def _proper_names(text: str) -> set[str]:
    """Lowercased proper-name tokens, minus common sentence-start words."""
    return {m.lower() for m in _PROPER_NAME_RE.findall(text) if m.lower() not in _COMMON_CAPS}


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

"""Per-verse sanity checks for modernizer output."""

from __future__ import annotations

import re

_PREAMBLE_PREFIXES = (
    "sure,", "sure ", "here is", "here's", "the verse", "the modernized",
    "modernized:", "output:", "translation:",
)

_PROPER_NAME_RE = re.compile(r"\b[A-Z][a-zA-Z'-]{2,}\b")

# Words that look like proper names but are common sentence-starters,
# common nouns, theological terms the LLM may lowercase, or abbreviations
# that are routinely modernized (e.g., "Jun." -> "Jr.").
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
    # Sentence-start common verbs/nouns observed as false positives in
    # data/failed.jsonl (see 2026-05-27 spec).
    "Jun", "Trifle", "Remember", "Lay", "Think", "Whoso", "Whosoever",
    "Presidency", "Concern", "According", "Forever", "Justice", "Gather",
    "Order", "Heart", "Pure", "State", "Stem", "May", "Higbee", "Questions",
    "Revelation", "What", "Esaias", "Amen", "Said", "Shall", "Was", "Die",
    "Cold", "Blood", "Innocent", "Murdered", "Angels",
    # Theological / institutional common nouns the LLM may legitimately
    # lowercase. We rely on the substring containment check (below) to still
    # catch outright drops.
    "Gospel", "Priesthood", "Covenant", "Atonement", "Ghost", "Cherubims",
    "Cherubim",
}}


def _candidate_names(text: str) -> list[str]:
    """Capitalized tokens from text that look like proper names.

    Returns original-case strings, deduped, minus _COMMON_CAPS.
    """
    seen = set()
    out = []
    for m in _PROPER_NAME_RE.findall(text):
        if m.lower() in _COMMON_CAPS:
            continue
        if m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out


def _normalize(token: str) -> str:
    """Lowercase and strip hyphens for substring matching."""
    return token.lower().replace("-", "")


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
    output_norm = _normalize(output)
    missing = sorted({
        name for name in _candidate_names(original)
        if _normalize(name) not in output_norm
    })
    if missing:
        return False, f"proper name(s) missing: {[n.lower() for n in missing]}"
    return True, ""

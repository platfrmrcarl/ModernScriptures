"""Deterministic regex-based fallback modernizer.

Used by the PDF renderer when an LLM-modernized form is unavailable
(verse.modernized is None). Performs literal word-level substitutions
from archaic English to modern English. Not a full translation -- just
enough to keep "thee/thou/hath/-eth" off the page.
"""

from __future__ import annotations

import re

# Each rule is a (compiled_pattern, replacement) pair. Order matters:
# more specific rules MUST come before generic ones (e.g., `saith` before
# any -eth rule, `thine <vowel>` before plain `thine`).
#
# All patterns use word boundaries (\b) to avoid mutating proper names
# (Elizabeth) or unrelated words (Other contains "the").
#
# Case handling: each rule is registered in two forms via _add() -- the
# lowercase form and the title-case form -- so "Thou" -> "You" and
# "thou" -> "you" both work without an IGNORECASE-with-case-rewriting
# scheme. ALL-CAPS forms (LORD, JEHOVAH) are intentionally NOT touched.

_RULES: list[tuple[re.Pattern[str], str]] = []


def _add(pattern: str, replacement: str) -> None:
    """Register a rule in both lowercase and title-case forms."""
    # Lowercase form.
    _RULES.append((re.compile(rf"\b{pattern}\b"), replacement))
    # Title-case form (capitalize both pattern and replacement first letter).
    cap_pat = pattern[0].upper() + pattern[1:]
    cap_rep = replacement[0].upper() + replacement[1:]
    _RULES.append((re.compile(rf"\b{cap_pat}\b"), cap_rep))


# --- Pronouns ---
# `thine` rules go FIRST (more specific lookahead first).
_RULES.append((
    re.compile(r"\bthine(\s+)(?=[aeiouAEIOU])"),
    r"your\1",
))
_RULES.append((
    re.compile(r"\bThine(\s+)(?=[aeiouAEIOU])"),
    r"Your\1",
))
_add("thine", "yours")
_add("thee", "you")
_add("thou", "you")
_add("thy", "your")
_add("ye", "you")

# --- Auxiliary verbs ---
_add("hath", "has")
_add("doth", "does")
_add("art", "are")
_add("shalt", "will")
_add("wilt", "will")
_add("mayst", "may")
_add("canst", "can")
_add("hast", "have")


def quick_modernize(text: str) -> str:
    """Apply all rules in order; return the modernized string."""
    for pattern, repl in _RULES:
        text = pattern.sub(repl, text)
    return text

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
# scheme. ALL-CAPS forms (LORD, JEHOVAH) are unaffected because we register only
# lowercase and title-case variants and regex is case-sensitive.

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
# Lookahead rules use a regex group and are appended manually -- _add() only
# handles plain word patterns with no groups.
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
# `art` is a verb only after a pronoun ("thou art" / "art thou"). After the
# pronoun rules above run, those become "you art" / "art you" (and the
# sentence-initial "Art thou" stays title-case as "Art you"). Match only
# those contexts so we don't mangle the noun ("the art of the apothecary").
_RULES.append((re.compile(r"\b(You|you)\s+art\b"), r"\1 are"))
_RULES.append((re.compile(r"\b(A|a)rt\s+(you|You)\b"), r"\1re \2"))
_add("shalt", "will")
# Same rationale as `art` above: `wilt` is a verb only in "thou wilt" /
# "wilt thou" context. After pronoun replacement that's "you wilt" /
# "wilt you" (and sentence-initial "Wilt thou" -> "Wilt you"). Match only
# those to avoid "flowers wilt" -> "flowers will".
_RULES.append((re.compile(r"\b(You|you)\s+wilt\b"), r"\1 will"))
_RULES.append((re.compile(r"\b(W|w)ilt\s+(you|You)\b"), r"\1ill \2"))
_add("mayst", "may")
_add("canst", "can")
_add("hast", "have")

# --- Explicit -eth endings (3rd person singular present) ---
# DO NOT add a generic \w+eth rule: it would mutate Elizabeth, meeketh, etc.
_add("saith", "says")
_add("cometh", "comes")
_add("goeth", "goes")
_add("knoweth", "knows")
_add("doeth", "does")

# --- Explicit -est endings (2nd person singular) ---
_add("knowest", "know")
_add("sayest", "say")
_add("doest", "do")
_add("believest", "believe")


def quick_modernize(text: str) -> str:
    """Apply all rules in order; return the modernized string."""
    for pattern, repl in _RULES:
        text = pattern.sub(repl, text)
    return text

"""System prompt and message builder for the modernizer."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are modernizing archaic English scripture into clear contemporary English \
in the style of the NIV or ESV. Rules:
- Replace thee/thou/thy/thine/ye and -eth/-est verb endings consistently \
throughout, including inside quoted dialogue and prayers.
- Replace archaic vocabulary (e.g. "wherefore" -> "therefore",
  "whence" -> "from where", "hither" -> "here", "saith" -> "says").
- Keep proper names exactly as written. Do not drop any name.
- Preserve EVERY capitalized noun from the input in your output, capitalized \
exactly as it appears. This includes plurals like "Gods", and theological \
terms like Priesthood, Gospel, Zion, Spirit, Ghost, Covenant, Atonement. If \
the source says "Gods" (plural), the output must say "Gods" (plural), not "God".
- Preserve theological terms when they have no plain equivalent \
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

EXAMPLE INPUT:
And the Gods organized and formed the heavens and the earth.

EXAMPLE OUTPUT:
And the Gods organized and formed the heavens and the earth.
"""


def build_messages(verse_text: str, retry_nudge: str | None = None) -> list[dict]:
    """Return Ollama-compatible messages for modernizing a single verse."""
    user = verse_text if not retry_nudge else f"{verse_text}\n\n{retry_nudge}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]

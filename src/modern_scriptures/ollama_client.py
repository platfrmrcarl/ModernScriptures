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

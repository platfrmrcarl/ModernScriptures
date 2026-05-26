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

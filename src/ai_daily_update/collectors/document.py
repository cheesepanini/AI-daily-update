from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    url: str
    title: str
    description: str
    text: str


def normalize_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in value.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceDocument:
    url: str
    title: str
    description: str
    text: str
    published: str = ""
    event_date_text: str = ""
    images: tuple[dict[str, str], ...] = ()
    image_license: str = ""
    publication_basis: str = ""
    links: tuple[dict[str, str], ...] = ()
    supplementary_sources: tuple[dict[str, str], ...] = ()


def normalize_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in value.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)

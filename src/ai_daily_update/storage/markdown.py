from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter


@dataclass
class MarkdownCard:
    path: Path
    metadata: dict[str, Any]
    content: str


def write_card(path: Path, metadata: dict[str, Any], content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(content, **metadata)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def read_card(path: Path) -> MarkdownCard:
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    return MarkdownCard(path=path, metadata=dict(post.metadata), content=post.content)


def update_metadata(path: Path, updates: dict[str, Any]) -> MarkdownCard:
    card = read_card(path)
    metadata = {**card.metadata, **updates}
    write_card(path, metadata, card.content)
    return read_card(path)


def iter_cards(markdown_root: Path) -> list[Path]:
    cards_root = markdown_root / "cards"
    if not cards_root.exists():
        return []
    return sorted(cards_root.rglob("*.md"))

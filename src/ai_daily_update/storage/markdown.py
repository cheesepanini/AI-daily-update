from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from ai_daily_update.utils.lock import exclusive_file_lock


@dataclass
class MarkdownCard:
    path: Path
    metadata: dict[str, Any]
    content: str


def write_card(path: Path, metadata: dict[str, Any], content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(content, **metadata)
    # Write to a temp file and rename into place so a crash or a concurrent
    # reader never observes a half-written/truncated card file.
    tmp_path = path.with_name(
        f".{path.name}.tmp-{os.getpid()}-{threading.get_ident()}-{uuid.uuid4().hex[:8]}"
    )
    tmp_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    os.replace(tmp_path, path)


def read_card(path: Path) -> MarkdownCard:
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    return MarkdownCard(path=path, metadata=dict(post.metadata), content=post.content)


def update_metadata(path: Path, updates: dict[str, Any]) -> MarkdownCard:
    lock_path = path.with_name(f".{path.name}.lock")
    with exclusive_file_lock(lock_path, blocking=True):
        card = read_card(path)
        metadata = {**card.metadata, **updates}
        write_card(path, metadata, card.content)
        return read_card(path)


def iter_cards(markdown_root: Path) -> list[Path]:
    cards_root = markdown_root / "cards"
    if not cards_root.exists():
        return []
    return sorted(cards_root.rglob("*.md"))

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path.cwd()


def ensure_directories(root: Path) -> None:
    for relative in [
        "config",
        "data/raw",
        "data/cache",
        "data/logs",
        "notes/inbox",
        "notes/cards",
        "notes/trash",
        "notes/topics",
        "notes/briefs/academic",
        "notes/briefs/industry",
        "notes/briefs/book",
        "notes/briefs/public",
    ]:
        (root / relative).mkdir(parents=True, exist_ok=True)

from __future__ import annotations

from pathlib import Path

from ai_daily_update.storage.markdown import read_card, update_metadata


def needs_review_cards(markdown_root: Path) -> list[Path]:
    cards_root = markdown_root / "cards"
    if not cards_root.exists():
        return []
    paths: list[Path] = []
    for path in sorted(cards_root.rglob("*.md")):
        card = read_card(path)
        if card.metadata.get("review_status") == "needs-review":
            paths.append(path)
    return paths


def set_review_status(path: Path, status: str) -> None:
    update_metadata(path, {"review_status": status})

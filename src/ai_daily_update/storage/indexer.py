from __future__ import annotations

from pathlib import Path

from ai_daily_update.storage import db
from ai_daily_update.storage.markdown import iter_cards, read_card


REQUIRED_ACCEPTED_FIELDS = ["source_url", "date", "topics", "review_status"]


def rebuild_index(markdown_root: Path, sqlite_path: Path) -> tuple[int, list[str]]:
    connection = db.connect(sqlite_path)
    try:
        with connection:
            db.reset_cards(connection)
            indexed = 0
            warnings: list[str] = []
            for path in iter_cards(markdown_root):
                card = read_card(path)
                if not card.metadata.get("id"):
                    warnings.append(f"{path}: missing id")
                    continue
                if card.metadata.get("review_status") == "accepted":
                    missing = [field for field in REQUIRED_ACCEPTED_FIELDS if not card.metadata.get(field)]
                    if missing:
                        warnings.append(f"{path}: accepted card missing {', '.join(missing)}")
                db.upsert_card(connection, path, card.metadata)
                indexed += 1
    finally:
        connection.close()
    return indexed, warnings

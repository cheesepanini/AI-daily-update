from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  track TEXT NOT NULL,
  title_zh TEXT,
  title_en TEXT,
  date TEXT NOT NULL,
  event_date TEXT,
  collected_date TEXT,
  source_type TEXT,
  source_url TEXT,
  primary_source INTEGER,
  topics TEXT NOT NULL,
  entities TEXT NOT NULL,
  importance INTEGER,
  novelty INTEGER,
  confidence INTEGER,
  book_potential INTEGER,
  ppt_potential INTEGER,
  public_brief_potential INTEGER,
  review_status TEXT NOT NULL,
  created_at TEXT
);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(SCHEMA)
    ensure_columns(connection)
    connection.commit()
    return connection


def ensure_columns(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(cards)").fetchall()
    }
    if "collected_date" not in columns:
        connection.execute("ALTER TABLE cards ADD COLUMN collected_date TEXT")
    if "event_date" not in columns:
        connection.execute("ALTER TABLE cards ADD COLUMN event_date TEXT")


def reset_cards(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM cards")
    connection.commit()


def upsert_card(connection: sqlite3.Connection, path: Path, metadata: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO cards (
          id, path, track, title_zh, title_en, date, event_date, collected_date, source_type, source_url,
          primary_source, topics, entities, importance, novelty, confidence,
          book_potential, ppt_potential, public_brief_potential, review_status,
          created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          path=excluded.path,
          track=excluded.track,
          title_zh=excluded.title_zh,
          title_en=excluded.title_en,
          date=excluded.date,
          event_date=excluded.event_date,
          collected_date=excluded.collected_date,
          source_type=excluded.source_type,
          source_url=excluded.source_url,
          primary_source=excluded.primary_source,
          topics=excluded.topics,
          entities=excluded.entities,
          importance=excluded.importance,
          novelty=excluded.novelty,
          confidence=excluded.confidence,
          book_potential=excluded.book_potential,
          ppt_potential=excluded.ppt_potential,
          public_brief_potential=excluded.public_brief_potential,
          review_status=excluded.review_status,
          created_at=excluded.created_at
        """,
        (
            metadata.get("id"),
            str(path),
            metadata.get("track", "academic"),
            metadata.get("title_zh", ""),
            metadata.get("title_en", ""),
            str(metadata.get("date", "")),
            str(metadata.get("event_date", "")),
            str(metadata.get("collected_date", metadata.get("date", ""))),
            metadata.get("source_type", ""),
            metadata.get("source_url", ""),
            1 if metadata.get("primary_source", True) else 0,
            json.dumps(metadata.get("topics", []), ensure_ascii=False),
            json.dumps(metadata.get("entities", []), ensure_ascii=False),
            metadata.get("importance"),
            metadata.get("novelty"),
            metadata.get("confidence"),
            metadata.get("book_potential"),
            metadata.get("ppt_potential"),
            metadata.get("public_brief_potential"),
            metadata.get("review_status", "needs-review"),
            metadata.get("created_at", ""),
        ),
    )
    connection.commit()


def query_cards(
    connection: sqlite3.Connection,
    from_date: str,
    to_date: str,
    topics: list[str] | None,
    audience: str,
    date_basis: str = "event",
) -> list[sqlite3.Row]:
    date_expression = (
        "COALESCE(collected_date, date)"
        if date_basis == "collected"
        else "COALESCE(NULLIF(event_date, ''), date)"
    )
    rows = connection.execute(
        f"""
        SELECT * FROM cards
        WHERE {date_expression} >= ?
          AND {date_expression} <= ?
          AND review_status = 'accepted'
        ORDER BY {date_expression} DESC, importance DESC, novelty DESC
        """,
        (from_date, to_date),
    ).fetchall()
    if topics:
        topic_set = set(topics)
        rows = [
            row
            for row in rows
            if topic_set.intersection(json.loads(row["topics"] or "[]"))
        ]
    if audience in {"academic", "industry"}:
        rows = [row for row in rows if row["track"] == audience]
    if audience == "public":
        rows = [row for row in rows if (row["public_brief_potential"] or 0) >= 3]
    return rows

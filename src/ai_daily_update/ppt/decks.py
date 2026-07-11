from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PPTDeck:
    id: str
    title: str
    version: str
    manuscript_path: Path
    csv_path: Path
    node_registry_path: Path

    @property
    def label(self) -> str:
        return f"{self.title}（{self.version}）" if self.version else self.title


def load_ppt_decks(root: Path) -> list[PPTDeck]:
    config_path = root / "ppt" / "decks.yaml"
    if not config_path.exists():
        return [default_ppt_deck(root)]
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    decks = []
    for item in raw.get("decks", []):
        deck_id = str(item.get("id", "")).strip()
        if not deck_id:
            continue
        decks.append(
            PPTDeck(
                id=deck_id,
                title=str(item.get("title", deck_id)).strip() or deck_id,
                version=str(item.get("version", "")).strip(),
                manuscript_path=root / str(item.get("manuscript_path", "")),
                csv_path=root / str(item.get("csv_path", "")),
                node_registry_path=root / str(item.get("node_registry_path", "")),
            )
        )
    return decks or [default_ppt_deck(root)]


def default_ppt_deck(root: Path) -> PPTDeck:
    deck_node_registry = root / "ppt" / "decks" / "ai-frontier-60min" / "nodes.yaml"
    legacy_node_registry = root / "ppt" / "ppt_nodes.yaml"
    return PPTDeck(
        id="ai-frontier-60min",
        title="人工智能发展前沿",
        version="60分钟版",
        manuscript_path=root / "ppt" / "ai_frontier_ppt_structured.md",
        csv_path=root / "ppt" / "ai_frontier_ppt_structured.csv",
        node_registry_path=deck_node_registry if deck_node_registry.exists() else legacy_node_registry,
    )


def selected_ppt_deck(root: Path, deck_id: str | None = None) -> PPTDeck:
    decks = load_ppt_decks(root)
    if deck_id:
        for deck in decks:
            if deck.id == deck_id:
                return deck
    return decks[0]


def deck_options(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "id": deck.id,
            "title": deck.title,
            "version": deck.version,
            "label": deck.label,
        }
        for deck in load_ppt_decks(root)
    ]

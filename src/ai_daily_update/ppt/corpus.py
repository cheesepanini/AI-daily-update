from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


@dataclass(frozen=True)
class PPTEntry:
    page: int
    level1: str
    level2: str
    level3: str
    content_type: str
    content: str


@dataclass(frozen=True)
class PPTTopicNode:
    key: tuple[str, str, str]
    level1: str
    level2: str
    level3: str
    pages: list[int]
    content: list[str]
    figure_notes: list[str]
    circled_items: list[str]

    @property
    def title_path(self) -> str:
        return " / ".join(part for part in [self.level1, self.level2, self.level3] if part)

    @property
    def text(self) -> str:
        return "\n".join(
            [self.level1, self.level2, self.level3, *self.content, *self.figure_notes, *self.circled_items]
        )


@dataclass(frozen=True)
class RegisteredPPTNode:
    node_id: str
    role: str
    intent: str
    current_level1: str
    current_level2: str
    current_level3: str
    keywords: list[str]
    update_policy: str = ""
    status: str = "active"

    @property
    def title_path(self) -> str:
        return " / ".join(
            part for part in [self.current_level1, self.current_level2, self.current_level3] if part
        )

    @property
    def text(self) -> str:
        return "\n".join([self.node_id, self.role, self.intent, self.title_path, *self.keywords])


@dataclass(frozen=True)
class PPTNodeMatch:
    registered: RegisteredPPTNode
    current: PPTTopicNode | None
    score: int
    reasons: list[str]


def read_ppt_entries(path: Path) -> list[PPTEntry]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        entries: list[PPTEntry] = []
        for row in reader:
            content = str(row.get("content", "")).strip()
            if not content:
                continue
            entries.append(
                PPTEntry(
                    page=safe_int(row.get("page", 0)),
                    level1=str(row.get("level1", "") or "").strip(),
                    level2=str(row.get("level2", "") or "").strip(),
                    level3=str(row.get("level3", "") or "").strip(),
                    content_type=str(row.get("content_type", "") or "content").strip(),
                    content=content,
                )
            )
    return entries


def group_ppt_topic_nodes(entries: list[PPTEntry]) -> list[PPTTopicNode]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry.level1, entry.level2, entry.level3)
        item = grouped.setdefault(
            key,
            {
                "level1": entry.level1,
                "level2": entry.level2,
                "level3": entry.level3,
                "pages": set(),
                "content": [],
                "figure_notes": [],
                "circled_items": [],
            },
        )
        if entry.page:
            item["pages"].add(entry.page)
        if entry.content_type == "figure_note":
            item["figure_notes"].append(entry.content)
        elif entry.content_type == "circled_item":
            item["circled_items"].append(entry.content)
        else:
            item["content"].append(entry.content)
    nodes = [
        PPTTopicNode(
            key=key,
            level1=item["level1"],
            level2=item["level2"],
            level3=item["level3"],
            pages=sorted(item["pages"]),
            content=item["content"],
            figure_notes=item["figure_notes"],
            circled_items=item["circled_items"],
        )
        for key, item in grouped.items()
    ]
    return sorted(nodes, key=lambda node: (node.pages[0] if node.pages else 9999, node.title_path))


def read_ppt_node_registry(path: Path) -> list[RegisteredPPTNode]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    nodes = []
    for item in raw.get("nodes", []):
        if not item.get("node_id"):
            continue
        nodes.append(
            RegisteredPPTNode(
                node_id=str(item.get("node_id", "")).strip(),
                role=str(item.get("role", "")).strip(),
                intent=str(item.get("intent", "")).strip(),
                current_level1=str(item.get("current_level1", "")).strip(),
                current_level2=str(item.get("current_level2", "")).strip(),
                current_level3=str(item.get("current_level3", "")).strip(),
                keywords=[str(keyword).strip() for keyword in item.get("keywords", []) if str(keyword).strip()],
                update_policy=str(item.get("update_policy", "")).strip(),
                status=str(item.get("status", "active")).strip() or "active",
            )
        )
    return nodes


def match_registered_nodes(
    registered_nodes: list[RegisteredPPTNode], current_nodes: list[PPTTopicNode]
) -> list[PPTNodeMatch]:
    matches = []
    for registered in registered_nodes:
        candidates = [
            score_registered_node_match(registered, current)
            for current in current_nodes
        ]
        best = max(candidates, key=lambda item: item.score, default=None)
        if best and best.score > 0:
            matches.append(best)
        else:
            matches.append(PPTNodeMatch(registered=registered, current=None, score=0, reasons=[]))
    return matches


def score_registered_node_match(
    registered: RegisteredPPTNode, current: PPTTopicNode
) -> PPTNodeMatch:
    score = 0
    reasons = []
    if registered.current_level1 and registered.current_level1 == current.level1:
        score += 8
        reasons.append("level1")
    if registered.current_level2 and registered.current_level2 == current.level2:
        score += 10
        reasons.append("level2")
    if registered.current_level3 and registered.current_level3 == current.level3:
        score += 12
        reasons.append("level3")
    keyword_hits = matching_terms(current.text, registered.keywords)
    if keyword_hits:
        score += min(len(keyword_hits), 5) * 3
        reasons.append("keywords:" + ",".join(keyword_hits[:5]))
    intent_hits = matching_terms(current.text, split_terms(registered.intent))
    if intent_hits:
        score += min(len(intent_hits), 3)
        reasons.append("intent")
    return PPTNodeMatch(registered=registered, current=current, score=score, reasons=reasons)


def matching_terms(text: str, terms: list[str]) -> list[str]:
    lower_text = text.lower()
    hits = []
    for term in terms:
        clean = term.strip()
        if not clean:
            continue
        if re.search(r"[A-Za-z0-9]", clean):
            if re.search(rf"\b{re.escape(clean.lower())}\b", lower_text):
                hits.append(clean)
        elif clean in text:
            hits.append(clean)
    return hits


def split_terms(text: str) -> list[str]:
    return [part for part in re.split(r"[\s，。；、/(),.]+", text) if len(part) >= 2]


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0

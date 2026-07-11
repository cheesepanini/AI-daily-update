from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ai_daily_update.config import Settings
from ai_daily_update.feedback.events import read_feedback_events
from ai_daily_update.source_proposals import read_source_proposals
from ai_daily_update.storage.markdown import iter_cards, read_card
from ai_daily_update.utils.dates import now_iso


FEATURE_VERSION = "v1"
SURFACES = {"cards", "ppt_suggestions", "source_proposals"}


def features_dir(root: Path) -> Path:
    return root / "data" / "features"


def feature_output_path(root: Path, surface: str) -> Path:
    return features_dir(root) / f"{surface}.jsonl"


def extract_preference_features(settings: Settings, surface: str = "all") -> list[Path]:
    surfaces = sorted(SURFACES) if surface == "all" else [surface]
    invalid = [item for item in surfaces if item not in SURFACES]
    if invalid:
        raise ValueError(f"unknown preference feature surface: {', '.join(invalid)}")
    labels = latest_feedback_labels(settings.root)
    written: list[Path] = []
    for item in surfaces:
        if item == "cards":
            records = card_feature_records(settings, labels)
        elif item == "ppt_suggestions":
            records = ppt_suggestion_feature_records(settings, labels)
        else:
            records = source_proposal_feature_records(settings, labels)
        written.append(write_feature_records(settings.root, item, records))
    return written


def write_feature_records(root: Path, surface: str, records: list[dict[str, Any]]) -> Path:
    path = feature_output_path(root, surface)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def read_feature_records(root: Path, surface: str) -> list[dict[str, Any]]:
    path = feature_output_path(root, surface)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_feedback_labels(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    labels: dict[tuple[str, str], dict[str, Any]] = {}
    for event in read_feedback_events(root):
        surface = label_surface(str(event.get("surface", "")))
        entity_id = str(event.get("entity_id", ""))
        if not surface or not entity_id:
            continue
        labels[(surface, entity_id)] = {
            "action": event.get("action", ""),
            "actor": event.get("actor", ""),
            "created_at": event.get("created_at", ""),
        }
    return labels


def label_surface(surface: str) -> str:
    return {
        "card_review": "cards",
        "auto_card_review": "cards",
        "ppt_suggestion_review": "ppt_suggestions",
        "source_proposal_review": "source_proposals",
    }.get(surface, "")


def card_feature_records(settings: Settings, labels: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for path in iter_cards(settings.markdown_root):
        card = read_card(path)
        metadata = card.metadata
        card_id = str(metadata.get("id") or path.stem)
        title = str(metadata.get("title_zh") or metadata.get("title_en") or "")
        topics = [str(topic) for topic in metadata.get("topics", []) or [] if str(topic)]
        source_url = str(metadata.get("source_url") or "")
        sections = markdown_headings(card.content)
        records.append(
            base_record(
                settings,
                "cards",
                card_id,
                labels,
                features={
                    "track": metadata.get("track", ""),
                    "review_status": metadata.get("review_status", ""),
                    "source_type": metadata.get("source_type", ""),
                    "source_domain": domain_for_url(source_url),
                    "topic_count": len(topics),
                    "topics": topics,
                    "title_length": len(title),
                    "content_length": len(card.content),
                    "heading_count": len(sections),
                    "has_one_sentence_conclusion": "一句话结论" in sections,
                    "has_event_overview": "事件概述" in sections,
                    "has_research_question": "研究问题" in sections,
                    "importance": safe_int(metadata.get("importance")),
                    "novelty": safe_int(metadata.get("novelty")),
                    "confidence": safe_int(metadata.get("confidence")),
                    "ppt_potential": safe_int(metadata.get("ppt_potential")),
                    "public_brief_potential": safe_int(metadata.get("public_brief_potential")),
                    "is_primary_source": metadata.get("primary_source") is True,
                    "is_digest_item": bool(metadata.get("digest_item_index")),
                },
                text={
                    "title": title,
                    "topics": " ".join(topics),
                    "source_url": source_url,
                },
            )
        )
    return records


def ppt_suggestion_feature_records(
    settings: Settings, labels: dict[tuple[str, str], dict[str, Any]]
) -> list[dict[str, Any]]:
    records = []
    for item in latest_ppt_plan_items(settings.markdown_root):
        suggestion_id = str(item.get("suggestion_id") or item.get("id") or "")
        if not suggestion_id:
            continue
        edits = item.get("edits", []) if isinstance(item.get("edits"), list) else []
        cards = item.get("cards", []) if isinstance(item.get("cards"), list) else []
        title = str(item.get("title") or item.get("recommendation") or suggestion_id)
        records.append(
            base_record(
                settings,
                "ppt_suggestions",
                suggestion_id,
                labels,
                features={
                    "kind": item.get("kind", ""),
                    "level1": item.get("level1", ""),
                    "level2": item.get("level2", ""),
                    "level3": item.get("level3", ""),
                    "card_count": len(cards),
                    "edit_count": len(edits),
                    "title_length": len(title),
                    "has_oral_text": bool(item.get("oral_text")),
                    "has_location": bool(item.get("location") or item.get("level2") or item.get("level3")),
                },
                text={
                    "title": title,
                    "recommendation": str(item.get("recommendation") or ""),
                    "location": str(item.get("location") or ""),
                },
            )
        )
    return records


def source_proposal_feature_records(
    settings: Settings, labels: dict[tuple[str, str], dict[str, Any]]
) -> list[dict[str, Any]]:
    records = []
    for proposal in read_source_proposals(settings.root):
        url = str(proposal.get("url") or "")
        proposal_id = stable_feature_id(url)
        records.append(
            base_record(
                settings,
                "source_proposals",
                proposal_id,
                labels,
                features={
                    "proposal_origin": proposal.get("proposal_origin", ""),
                    "priority": proposal.get("priority", ""),
                    "primary_topic": proposal.get("primary_topic", ""),
                    "secondary_topic": proposal.get("secondary_topic", ""),
                    "source_domain": domain_for_url(url),
                    "score": safe_int(proposal.get("score")),
                    "reason_length": len(str(proposal.get("reason") or "")),
                    "coverage_length": len(str(proposal.get("coverage") or "")),
                },
                text={
                    "name": str(proposal.get("name") or ""),
                    "url": url,
                    "reason": str(proposal.get("reason") or ""),
                },
            )
        )
    return records


def base_record(
    settings: Settings,
    surface: str,
    entity_id: str,
    labels: dict[tuple[str, str], dict[str, Any]],
    features: dict[str, Any],
    text: dict[str, str],
) -> dict[str, Any]:
    return {
        "surface": surface,
        "entity_id": entity_id,
        "feature_version": FEATURE_VERSION,
        "extracted_at": now_iso(settings.timezone),
        "label": labels.get((surface, entity_id), {}),
        "features": features,
        "text": text,
    }


def latest_ppt_plan_items(markdown_root: Path) -> list[dict[str, Any]]:
    inbox = markdown_root / "inbox"
    if not inbox.exists():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(inbox.glob("*ppt-update-plan*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        raw_items = data.get("items", [])
        if isinstance(raw_items, list):
            for item in raw_items:
                if isinstance(item, dict):
                    item = dict(item)
                    item.setdefault("report_path", str(path))
                    items.append(item)
    return items


def markdown_headings(content: str) -> set[str]:
    headings = set()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            headings.add(stripped.removeprefix("## ").strip())
    return headings


def domain_for_url(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def stable_feature_id(value: str) -> str:
    import hashlib

    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]

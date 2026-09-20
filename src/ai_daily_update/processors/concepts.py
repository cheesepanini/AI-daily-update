from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FoundationalConcept:
    id: str
    name_zh: str
    name_en: str
    category: str
    aliases: list[str]
    applies_to_topics: list[str]


def load_foundational_concepts(concepts_config: dict[str, Any]) -> list[FoundationalConcept]:
    concepts = concepts_config.get("concepts", {}) or {}
    return [
        FoundationalConcept(
            id=concept_id,
            name_zh=str(info.get("name_zh", "")),
            name_en=str(info.get("name_en", "")),
            category=str(info.get("category", "")),
            aliases=[str(alias) for alias in info.get("aliases", []) or []],
            applies_to_topics=[str(topic) for topic in info.get("applies_to_topics", []) or []],
        )
        for concept_id, info in concepts.items()
    ]


def match_foundational_concepts(
    metadata: dict[str, Any], content: str, concepts_config: dict[str, Any], limit: int = 6
) -> list[dict[str, str]]:
    """Match a card to foundational concepts a reader needs to understand it.

    Keyword-only (no LLM calls), mirroring the scoring style of
    classify_candidate_topics and retrieval.title_terms. An alias hit in the
    title/content is REQUIRED — a card's topics (e.g. "foundation-model")
    cover the large majority of cards, so topic overlap alone would surface
    the same handful of concepts on nearly every card. Topic overlap only
    adds ranking weight on top of an actual keyword match.
    """
    card_topics = set(metadata.get("topics", []) or [])
    text = f"{metadata.get('title_zh', '')} {metadata.get('title_en', '')} {content}".lower()
    category_labels = concepts_config.get("category_labels", {}) or {}

    scored: list[tuple[int, FoundationalConcept]] = []
    for concept in load_foundational_concepts(concepts_config):
        alias_hits = sum(1 for alias in concept.aliases if alias.lower() in text)
        if alias_hits <= 0:
            continue
        score = alias_hits * 3 + len(card_topics.intersection(concept.applies_to_topics)) * 2
        scored.append((score, concept))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            "id": concept.id,
            "name_zh": concept.name_zh,
            "name_en": concept.name_en,
            "category": concept.category,
            "category_label": category_labels.get(concept.category, concept.category),
        }
        for _, concept in scored[:limit]
    ]

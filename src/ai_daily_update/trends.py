from __future__ import annotations

import re
from typing import Any


TREND_TERMS = [
    "智能体",
    "基础模型",
    "自监督训练",
    "空间智能",
    "公开测评",
    "榜单",
    "世界模型",
    "多模态",
    "推理",
    "安全",
    "遗忘",
    "成本",
    "定价",
    "长上下文",
    "视频生成",
    "编程智能体",
    "AI coding",
    "agent",
    "leaderboard",
    "benchmark",
    "world model",
    "multimodal",
    "reasoning",
]

TREND_SYNONYM_GROUPS = {
    "foundation-model": ["基础模型", "大模型", "预训练大模型", "foundation model", "LLM"],
    "self-supervised-learning": ["自监督训练", "自监督学习", "self-supervised learning"],
    "spatial-intelligence": ["空间智能", "spatial intelligence", "spatial reasoning"],
    "agent": ["智能体", "编程智能体", "agent", "AI agent", "AI Agents", "AI coding"],
    "benchmark-evaluation": ["公开测评", "榜单", "leaderboard", "benchmark", "evaluation"],
    "generative-model": ["视频生成", "多模态", "world model", "世界模型", "multimodal"],
}

TREND_AD_HOC_GROUPS = [
    {
        "id": "reasoning",
        "label": "推理",
        "terms": ["推理", "reasoning"],
    },
]


def trend_term_groups(topics_config: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    grouped_terms: set[str] = set()
    topics = topics_config.get("topics", {})
    for topic_id, topic in topics.items():
        terms = topic_terms(topic_id, topic)
        terms.extend(TREND_SYNONYM_GROUPS.get(topic_id, []))
        unique_terms = unique_casefolded_terms(terms)
        for term in unique_terms:
            grouped_terms.add(term.lower())
        groups.append(
            {
                "id": topic_id,
                "label": topic.get("name_zh") or topic.get("name_en") or topic_id,
                "terms": unique_terms,
                "aliases": display_aliases(unique_terms),
                "configured": True,
            }
        )
    for group in TREND_AD_HOC_GROUPS:
        unique_terms = unique_casefolded_terms(group["terms"])
        for term in unique_terms:
            grouped_terms.add(term.lower())
        groups.append(
            {
                "id": group["id"],
                "label": group["label"],
                "terms": unique_terms,
                "aliases": display_aliases(unique_terms),
                "configured": False,
            }
        )
    for term in TREND_TERMS:
        if term.lower() in grouped_terms:
            continue
        groups.append(
            {
                "id": term,
                "label": term,
                "terms": [term],
                "aliases": [],
                "configured": False,
            }
        )
    return groups


def topic_terms(topic_id: str, topic: dict[str, Any]) -> list[str]:
    terms = [topic_id]
    for key in ["name_zh", "name_en"]:
        if topic.get(key):
            terms.append(str(topic[key]))
    terms.extend(str(alias) for alias in topic.get("aliases", []))
    return terms


def unique_casefolded_terms(terms: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = " ".join(str(term).split())
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(normalized)
    return unique


def display_aliases(terms: list[str], limit: int = 6) -> list[str]:
    return sorted(terms, key=lambda term: (re.search(r"[A-Za-z]", term) is None, term.lower()))[:limit]


def trend_group_count(text: str, terms: list[str]) -> int:
    matches: list[tuple[int, int]] = []
    for term in terms:
        matches.extend(trend_matches(text, term))
    selected: list[tuple[int, int]] = []
    for start, end in sorted(matches, key=lambda span: (span[1] - span[0]), reverse=True):
        if any(start < existing_end and end > existing_start for existing_start, existing_end in selected):
            continue
        selected.append((start, end))
    return len(selected)


def trend_matches(text: str, term: str) -> list[tuple[int, int]]:
    if re.search(r"[A-Za-z]", term):
        return [
            match.span()
            for match in re.finditer(rf"\b{re.escape(term.lower())}\b", text.lower())
        ]
    return [match.span() for match in re.finditer(re.escape(term), text)]


def trend_count(text: str, term: str) -> int:
    if re.search(r"[A-Za-z]", term):
        return len(re.findall(rf"\b{re.escape(term.lower())}\b", text.lower()))
    return text.count(term)

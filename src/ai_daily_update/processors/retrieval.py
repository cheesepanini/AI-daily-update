from __future__ import annotations

import re
from pathlib import Path

from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.reports.brief import extract_sections, first_available
from ai_daily_update.storage.markdown import iter_cards, read_card


def find_related_cards(
    candidate: Candidate, markdown_root: Path, limit: int = 3
) -> list[dict[str, str]]:
    """Find existing cards related to a candidate, by topic and title overlap.

    Keyword/topic overlap only (no embeddings) to match the scoring style
    already used by the PPT planning module (ppt/corpus.py, ppt/plan.py).
    """
    candidate_topics = set(candidate.topics)
    candidate_terms = title_terms(candidate.title)
    scored: list[tuple[int, dict[str, str]]] = []
    for path in iter_cards(markdown_root):
        card = read_card(path)
        metadata = card.metadata
        if metadata.get("review_status") == "rejected":
            continue
        if metadata.get("url") == candidate.url or metadata.get("source_url") == candidate.url:
            continue
        score = related_card_score(candidate_topics, candidate_terms, metadata)
        if score <= 0:
            continue
        sections = extract_sections(card.content)
        title = metadata.get("title_zh") or metadata.get("title_en") or metadata.get("id", "")
        scored.append(
            (
                score,
                {
                    "title": str(title),
                    "date": str(metadata.get("date", "")),
                    "conclusion": first_available(sections, ["一句话结论"], fallback=""),
                },
            )
        )
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def related_card_score(
    candidate_topics: set[str], candidate_terms: set[str], metadata: dict
) -> int:
    topic_overlap = len(candidate_topics.intersection(metadata.get("topics", []) or []))
    score = topic_overlap * 3
    card_title = f"{metadata.get('title_zh', '')} {metadata.get('title_en', '')}"
    score += len(candidate_terms.intersection(title_terms(card_title)))
    return score


def find_duplicate_suspect(candidate: Candidate, markdown_root: Path) -> dict[str, str] | None:
    """Flag an existing card that may report the same event as this candidate.

    Deliberately conservative (requires topic overlap AND >=30% of the
    smaller title's terms in common, where terms are character bigrams for
    Chinese segments) because false positives here surface a warning to a
    human reviewer, not an automatic skip. Calibrated against the local card
    corpus: at this threshold genuinely-related pairs (e.g. two write-ups of
    the same product launch, even when phrased very differently) are
    flagged, while topically-adjacent but distinct items (e.g. two unrelated
    KV-cache compression papers) are not.
    """
    candidate_topics = set(candidate.topics)
    candidate_terms = title_terms(candidate.title)
    if not candidate_terms:
        return None
    best: tuple[float, dict[str, str]] | None = None
    for path in iter_cards(markdown_root):
        card = read_card(path)
        metadata = card.metadata
        if metadata.get("review_status") == "rejected":
            continue
        if metadata.get("url") == candidate.url or metadata.get("source_url") == candidate.url:
            continue
        card_topics = set(metadata.get("topics", []) or [])
        if not candidate_topics.intersection(card_topics):
            continue
        card_title = f"{metadata.get('title_zh', '')} {metadata.get('title_en', '')}"
        card_terms = title_terms(card_title)
        if not card_terms:
            continue
        overlap = candidate_terms.intersection(card_terms)
        if not overlap:
            continue
        min_ratio = len(overlap) / min(len(candidate_terms), len(card_terms))
        if min_ratio < 0.3:
            continue
        title = metadata.get("title_zh") or metadata.get("title_en") or metadata.get("id", "")
        match = {
            "title": str(title),
            "date": str(metadata.get("date", "")),
            "source_url": str(metadata.get("source_url", "")),
        }
        if best is None or min_ratio > best[0]:
            best = (min_ratio, match)
    return best[1] if best else None


_SPLIT_RE = re.compile(
    r"[\s，。！？；、《》「」『』【】(){}\[\]（）,.:：\-—/|*·~～\"'&%]+"
)
_ASCII_RUN_RE = re.compile(r"[a-z0-9]+")


def title_terms(title: str) -> set[str]:
    """Break a title into comparable terms for overlap scoring.

    Chinese titles rarely contain the punctuation this used to split on, so
    splitting alone leaves whole clauses as single unsplittable "terms" and
    overlap becomes mostly luck of the punctuation. Chinese segments are
    character-bigrammed instead (a standard low-cost stand-in for word
    segmentation); ASCII/digit runs (model names, version numbers) are kept
    whole so e.g. "WAM-TTT" or "GLM-6" survive as a single distinguishing
    token rather than being shredded into meaningless bigrams.
    """
    terms: set[str] = set()
    for chunk in _SPLIT_RE.split(title.lower()):
        if not chunk:
            continue
        pos = 0
        for match in _ASCII_RUN_RE.finditer(chunk):
            cjk = chunk[pos : match.start()]
            _add_bigrams(terms, cjk)
            terms.add(match.group())
            pos = match.end()
        _add_bigrams(terms, chunk[pos:])
    return terms


def _add_bigrams(terms: set[str], segment: str) -> None:
    if len(segment) >= 2:
        terms.update(segment[i : i + 2] for i in range(len(segment) - 1))
    elif segment:
        terms.add(segment)

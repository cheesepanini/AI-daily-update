from __future__ import annotations

from ai_daily_update.processors.candidates import Candidate, with_updates
from ai_daily_update.utils.config import section


SOURCE_WEIGHTS = {
    "manual": 30,
    "arxiv": 16,
    "company_blog": 12,
    "rss": 10,
}


def score_candidate(
    candidate: Candidate, topics_config: dict, scoring_config: dict | None = None
) -> Candidate:
    candidate_scoring = section(scoring_config, "candidate_scoring")
    source_weights = candidate_scoring.get("source_weights") or SOURCE_WEIGHTS
    topic_multiplier = int(candidate_scoring.get("topic_priority_multiplier", 10))
    bonuses = section(candidate_scoring, "bonuses")
    reasons: list[str] = []
    score = int(source_weights.get(candidate.source_kind, 5))
    reasons.append(f"source:{candidate.source_kind}+{score}")
    topic_priority = 0
    for topic in candidate.topics:
        priority = int(section(section(topics_config, "topics"), topic).get("priority", 1))
        topic_priority = max(topic_priority, priority)
    topic_points = topic_priority * topic_multiplier
    score += topic_points
    reasons.append(f"topic_priority:{topic_priority}+{topic_points}")
    if candidate.summary:
        summary_bonus = int(bonuses.get("summary", 4))
        score += summary_bonus
        reasons.append(f"summary+{summary_bonus}")
    if candidate.published:
        published_bonus = int(bonuses.get("published", 2))
        score += published_bonus
        reasons.append(f"published+{published_bonus}")
    return with_updates(candidate, score=float(score), score_reasons=tuple(reasons))


def select_top_candidates(
    candidates: list[Candidate],
    max_cards: int,
    academic_quota: int,
    industry_quota: int,
) -> list[Candidate]:
    sorted_candidates = sorted(candidates, key=lambda item: item.score, reverse=True)
    selected: list[Candidate] = []
    counts = {"academic": 0, "industry": 0}
    quotas = {"academic": academic_quota, "industry": industry_quota}
    for candidate in sorted_candidates:
        if len(selected) >= max_cards:
            break
        quota = quotas.get(candidate.track)
        if quota is not None and counts.get(candidate.track, 0) >= quota:
            continue
        selected.append(candidate)
        counts[candidate.track] = counts.get(candidate.track, 0) + 1
    for candidate in sorted_candidates:
        if len(selected) >= max_cards:
            break
        if candidate in selected:
            continue
        selected.append(candidate)
    return selected


def select_top_media_candidates(candidates: list[Candidate], media_quota: int) -> list[Candidate]:
    media_candidates = [
        candidate for candidate in candidates if candidate.source_kind == "chinese_media"
    ]
    return sorted(media_candidates, key=lambda item: item.score, reverse=True)[:media_quota]

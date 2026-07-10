from __future__ import annotations

from ai_daily_update.processors.candidates import Candidate, with_updates


def classify_candidate_topics(candidate: Candidate, topics_config: dict) -> Candidate:
    if candidate.topics:
        return candidate
    text = f"{candidate.title}\n{candidate.summary}".lower()
    matched: list[tuple[int, str]] = []
    topics = topics_config.get("topics", {})
    for topic_id, topic_info in topics.items():
        tracks = topic_info.get("track", [])
        if candidate.track not in tracks:
            continue
        aliases = topic_info.get("aliases", [])
        names = [topic_info.get("name_en", ""), topic_info.get("name_zh", "")]
        terms = [term for term in [*aliases, *names, topic_id] if term]
        if any(term.lower() in text for term in terms):
            matched.append((int(topic_info.get("priority", 1)), topic_id))
    matched.sort(reverse=True)
    if matched:
        return with_updates(candidate, topics=[topic_id for _, topic_id in matched[:3]])
    fallback = "ai-industry" if candidate.track == "industry" else "foundation-model"
    return with_updates(candidate, topics=[fallback])

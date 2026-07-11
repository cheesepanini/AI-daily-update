from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from ai_daily_update.storage.markdown import iter_cards, read_card, update_metadata
from ai_daily_update.utils.dates import now_iso


@dataclass(frozen=True)
class AutoReviewDecision:
    path: Path
    card_id: str
    title: str
    status: str
    score: int
    age_days: int
    reasons: list[str]


def auto_review_stale_cards(
    markdown_root: Path,
    topics_config: dict[str, Any],
    review_config: dict[str, Any],
    run_day: date,
    timezone: str,
    dry_run: bool = False,
) -> list[AutoReviewDecision]:
    auto_config = review_config.get("auto", {})
    stale_after_days = int(auto_config.get("stale_after_days", 1))
    accept_threshold = int(auto_config.get("accept_threshold", 28))
    reject_threshold = int(auto_config.get("reject_threshold", 22))
    uncertain_status = str(auto_config.get("uncertain_status", "rejected") or "rejected")
    decisions: list[AutoReviewDecision] = []
    for path in iter_cards(markdown_root):
        card = read_card(path)
        metadata = card.metadata
        if metadata.get("review_status") != "needs-review":
            continue
        age_days = card_age_days(metadata, run_day)
        if age_days < stale_after_days:
            continue
        score, reasons = auto_review_score(metadata, topics_config)
        if score >= accept_threshold:
            status = "accepted"
            reasons.append(f"score>={accept_threshold}: 自动接受")
        elif score <= reject_threshold:
            status = "rejected"
            reasons.append(f"score<={reject_threshold}: 自动拒绝")
        else:
            status = uncertain_status
            reasons.append(f"{reject_threshold}<score<{accept_threshold}: 信号不够强，按配置设为 {uncertain_status}")
        title = str(metadata.get("title_zh") or metadata.get("title_en") or metadata.get("id") or path.stem)
        decision = AutoReviewDecision(
            path=path,
            card_id=str(metadata.get("id", path.stem)),
            title=title,
            status=status,
            score=score,
            age_days=age_days,
            reasons=reasons,
        )
        decisions.append(decision)
        if not dry_run:
            update_metadata(
                path,
                {
                    "review_status": status,
                    "reviewed_by": "auto",
                    "reviewed_at": now_iso(timezone),
                    "auto_review_score": score,
                    "auto_review_age_days": age_days,
                    "auto_review_reasons": reasons,
                },
            )
    return decisions


def auto_review_score(metadata: dict[str, Any], topics_config: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    score += weighted_numeric(metadata, "importance", 2, reasons)
    score += weighted_numeric(metadata, "novelty", 2, reasons)
    score += weighted_numeric(metadata, "confidence", 2, reasons)
    score += weighted_numeric(metadata, "ppt_potential", 1, reasons)
    score += weighted_numeric(metadata, "public_brief_potential", 1, reasons)
    topic_priority = max_topic_priority(metadata.get("topics", []), topics_config)
    if topic_priority:
        points = topic_priority * 2
        score += points
        reasons.append(f"topic_priority:{topic_priority}+{points}")
    source_type = str(metadata.get("source_type", ""))
    if source_type in {"paper", "company-news", "benchmark-update"}:
        score += 2
        reasons.append(f"source_type:{source_type}+2")
    elif source_type in {"chinese-media", "chinese-media-digest-item"}:
        score -= 2
        reasons.append(f"source_type:{source_type}-2")
    if metadata.get("primary_source") is True:
        score += 2
        reasons.append("primary_source+2")
    if not metadata.get("source_url"):
        score -= 3
        reasons.append("missing_source_url-3")
    return score, reasons


def weighted_numeric(metadata: dict[str, Any], key: str, weight: int, reasons: list[str]) -> int:
    value = safe_int(metadata.get(key), 0)
    points = value * weight
    if points:
        reasons.append(f"{key}:{value}+{points}")
    return points


def max_topic_priority(topics: Any, topics_config: dict[str, Any]) -> int:
    if not isinstance(topics, list):
        return 0
    configured = topics_config.get("topics", {})
    priorities = [
        safe_int(configured.get(str(topic), {}).get("priority"), 1)
        for topic in topics
        if str(topic)
    ]
    return max(priorities, default=0)


def card_age_days(metadata: dict[str, Any], run_day: date) -> int:
    card_date = parse_card_date(metadata)
    if not card_date:
        return 0
    return max((run_day - card_date).days, 0)


def parse_card_date(metadata: dict[str, Any]) -> date | None:
    for key in ["collected_date", "created_at", "date"]:
        raw_value = metadata.get(key)
        if not raw_value:
            continue
        parsed = parse_date_value(str(raw_value))
        if parsed:
            return parsed
    return None


def parse_date_value(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default

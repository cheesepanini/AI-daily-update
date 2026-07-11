from datetime import date

from ai_daily_update.review.auto import auto_review_stale_cards, safe_int
from ai_daily_update.storage.markdown import read_card, write_card


def test_safe_int_handles_infinity_without_crashing() -> None:
    assert safe_int(float("inf")) == 0
    assert safe_int(float("-inf")) == 0
    assert safe_int(float("nan")) == 0


TOPICS = {
    "topics": {
        "foundation-model": {"priority": 5},
        "general-ai": {"priority": 1},
    }
}

REVIEW_CONFIG = {
    "auto": {
        "enabled": True,
        "stale_after_days": 1,
        "accept_threshold": 28,
        "reject_threshold": 22,
        "uncertain_status": "rejected",
    }
}


def test_auto_review_accepts_stale_high_signal_card(tmp_path) -> None:
    path = tmp_path / "notes" / "cards" / "2026" / "07" / "strong.md"
    write_card(
        path,
        {
            "id": "strong",
            "title_zh": "强信号卡片",
            "date": "2026-07-05",
            "collected_date": "2026-07-05",
            "source_url": "https://example.com",
            "source_type": "paper",
            "topics": ["foundation-model"],
            "importance": 4,
            "novelty": 4,
            "confidence": 4,
            "ppt_potential": 4,
            "public_brief_potential": 4,
            "primary_source": True,
            "review_status": "needs-review",
        },
        "content",
    )

    decisions = auto_review_stale_cards(
        tmp_path / "notes",
        TOPICS,
        REVIEW_CONFIG,
        date(2026, 7, 7),
        "Asia/Shanghai",
    )

    assert len(decisions) == 1
    assert decisions[0].status == "accepted"
    card = read_card(path)
    assert card.metadata["review_status"] == "accepted"
    assert card.metadata["reviewed_by"] == "auto"
    assert card.metadata["auto_review_score"] >= 28


def test_auto_review_rejects_stale_low_signal_card(tmp_path) -> None:
    path = tmp_path / "notes" / "cards" / "2026" / "07" / "weak.md"
    write_card(
        path,
        {
            "id": "weak",
            "title_zh": "弱信号卡片",
            "date": "2026-07-05",
            "collected_date": "2026-07-05",
            "topics": ["general-ai"],
            "importance": 1,
            "novelty": 1,
            "confidence": 1,
            "ppt_potential": 1,
            "public_brief_potential": 1,
            "review_status": "needs-review",
        },
        "content",
    )

    decisions = auto_review_stale_cards(
        tmp_path / "notes",
        TOPICS,
        REVIEW_CONFIG,
        date(2026, 7, 7),
        "Asia/Shanghai",
    )

    assert len(decisions) == 1
    assert decisions[0].status == "rejected"
    assert read_card(path).metadata["review_status"] == "rejected"


def test_auto_review_processes_cards_waiting_one_day(tmp_path) -> None:
    path = tmp_path / "notes" / "cards" / "2026" / "07" / "recent.md"
    write_card(
        path,
        {
            "id": "recent",
            "date": "2026-07-06",
            "collected_date": "2026-07-06",
            "topics": ["foundation-model"],
            "review_status": "needs-review",
        },
        "content",
    )

    decisions = auto_review_stale_cards(
        tmp_path / "notes",
        TOPICS,
        REVIEW_CONFIG,
        date(2026, 7, 7),
        "Asia/Shanghai",
    )

    assert len(decisions) == 1
    assert read_card(path).metadata["review_status"] == "rejected"


def test_auto_review_skips_same_day_cards(tmp_path) -> None:
    path = tmp_path / "notes" / "cards" / "2026" / "07" / "same-day.md"
    write_card(
        path,
        {
            "id": "same-day",
            "date": "2026-07-07",
            "collected_date": "2026-07-07",
            "topics": ["foundation-model"],
            "review_status": "needs-review",
        },
        "content",
    )

    decisions = auto_review_stale_cards(
        tmp_path / "notes",
        TOPICS,
        REVIEW_CONFIG,
        date(2026, 7, 7),
        "Asia/Shanghai",
    )

    assert decisions == []
    assert read_card(path).metadata["review_status"] == "needs-review"


def test_auto_review_dry_run_does_not_update_card(tmp_path) -> None:
    path = tmp_path / "notes" / "cards" / "2026" / "07" / "dry.md"
    write_card(
        path,
        {
            "id": "dry",
            "date": "2026-07-05",
            "collected_date": "2026-07-05",
            "source_url": "https://example.com",
            "source_type": "paper",
            "topics": ["foundation-model"],
            "importance": 4,
            "novelty": 4,
            "confidence": 4,
            "ppt_potential": 4,
            "public_brief_potential": 4,
            "review_status": "needs-review",
        },
        "content",
    )

    decisions = auto_review_stale_cards(
        tmp_path / "notes",
        TOPICS,
        REVIEW_CONFIG,
        date(2026, 7, 7),
        "Asia/Shanghai",
        dry_run=True,
    )

    assert len(decisions) == 1
    assert read_card(path).metadata["review_status"] == "needs-review"

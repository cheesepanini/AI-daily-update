from datetime import date

from ai_daily_update.processors.card_builder import (
    apply_content_date,
    build_card_metadata,
    candidate_date,
    infer_date_from_content,
)
from ai_daily_update.processors.candidates import Candidate


def test_build_card_metadata_uses_candidate_published_date() -> None:
    candidate = Candidate(
        url="https://arxiv.org/abs/2607.02514v1",
        track="academic",
        topics=["foundation-model"],
        title="Distributed Attacks",
        published="2026-07-02T12:34:56Z",
    )

    metadata = build_card_metadata(candidate, date(2026, 7, 7), "Asia/Shanghai")

    assert metadata["date"] == "2026-07-02"
    assert metadata["collected_date"] == "2026-07-07"
    assert metadata["id"].startswith("2026-07-02-academic-foundation-model")


def test_build_card_metadata_uses_benchmark_source_type() -> None:
    candidate = Candidate(
        url="https://arena.ai/blog/leaderboard-changelog",
        track="industry",
        topics=["benchmark-evaluation"],
        title="Leaderboard changelog",
        source_kind="benchmark",
    )

    metadata = build_card_metadata(candidate, date(2026, 7, 7), "Asia/Shanghai")

    assert metadata["source_type"] == "benchmark-update"


def test_build_card_metadata_records_digest_parent_source() -> None:
    candidate = Candidate(
        url="https://m.sohu.com/a/1_455313?digest_item=2",
        track="industry",
        topics=["agent"],
        title="腾讯混元Hy3发布，Agent与产品体验升级",
        source_kind="chinese_media",
        source_name="腾讯研究院",
        parent_url="https://m.sohu.com/a/1_455313",
        parent_title="腾讯研究院AI速递 20260707",
        digest_item_index=2,
    )

    metadata = build_card_metadata(candidate, date(2026, 7, 7), "Asia/Shanghai")

    assert metadata["source_type"] == "chinese-media-digest-item"
    assert metadata["parent_source_url"] == "https://m.sohu.com/a/1_455313"
    assert metadata["parent_source_title"] == "腾讯研究院AI速递 20260707"
    assert metadata["digest_item_index"] == 2


def test_candidate_date_parses_rfc822_rss_dates() -> None:
    candidate = Candidate(
        url="https://example.com/post",
        track="industry",
        topics=["ai-industry"],
        title="Post",
        published="Tue, 23 Jun 2026 10:00:00 GMT",
    )

    assert candidate_date(candidate, fallback=date(2026, 7, 7)) == date(2026, 6, 23)


def test_candidate_date_falls_back_to_run_date() -> None:
    candidate = Candidate(
        url="https://example.com/post",
        track="industry",
        topics=["ai-industry"],
        title="Post",
    )

    assert candidate_date(candidate, fallback=date(2026, 7, 7)) == date(2026, 7, 7)


def test_infer_date_from_content_reads_chinese_publish_date() -> None:
    content = "2026 年 6 月 23 日，Anthropic 发布了 Claude Tag。"

    assert infer_date_from_content(content) == date(2026, 6, 23)


def test_apply_content_date_updates_metadata_when_candidate_has_no_published_date() -> None:
    candidate = Candidate(
        url="https://www.anthropic.com/news/introducing-claude-tag",
        track="industry",
        topics=["ai-industry"],
        title="Introducing Claude Tag",
    )
    metadata = build_card_metadata(candidate, date(2026, 7, 7), "Asia/Shanghai")
    content = """
## 事件概述
2026 年 6 月 23 日，Anthropic 发布了 Claude Tag。
"""

    updated = apply_content_date(metadata, candidate, content)

    assert updated["date"] == "2026-06-23"
    assert updated["event_date"] == "2026-06-23"
    assert updated["collected_date"] == "2026-07-07"
    assert updated["id"].startswith("2026-06-23-industry-ai-industry")


def test_apply_content_date_keeps_published_date_and_records_event_date() -> None:
    candidate = Candidate(
        url="https://example.com/news",
        track="industry",
        topics=["ai-industry"],
        title="Company News",
        published="2026-07-08T08:00:00Z",
    )
    metadata = build_card_metadata(candidate, date(2026, 7, 8), "Asia/Shanghai")
    content = """
## 事件概述
2026 年 6 月 4 日，公司宣布成立新实验室。
"""

    updated = apply_content_date(metadata, candidate, content)

    assert updated["date"] == "2026-07-08"
    assert updated["event_date"] == "2026-06-04"
    assert updated["id"].startswith("2026-07-08-industry-ai-industry")

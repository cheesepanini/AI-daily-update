from ai_daily_update.collectors.company_blogs import CompanyBlogItem
from ai_daily_update.collectors.rss import RSSItem
from ai_daily_update.cli import candidates_for_generation
from ai_daily_update.processors.candidates import (
    Candidate,
    candidate_from_company_item,
    candidate_from_rss_item,
)
from ai_daily_update.processors.classify import classify_candidate_topics
from ai_daily_update.processors.score import (
    score_candidate,
    select_top_candidates,
    select_top_media_candidates,
)


TOPICS_CONFIG = {
    "topics": {
        "agent": {
            "track": ["academic", "industry"],
            "priority": 5,
            "aliases": ["agent", "agents"],
        },
        "ai-industry": {
            "track": ["industry"],
            "priority": 5,
            "aliases": ["enterprise ai"],
        },
        "foundation-model": {
            "track": ["academic", "industry"],
            "priority": 5,
            "aliases": ["foundation model", "large language model"],
        },
    }
}


def test_classify_candidate_topics_uses_aliases() -> None:
    candidate = Candidate(
        url="https://example.com",
        track="industry",
        topics=[],
        title="New agent platform for enterprise AI",
    )

    classified = classify_candidate_topics(candidate, TOPICS_CONFIG)

    assert classified.topics == ["ai-industry", "agent"]


def test_score_candidate_uses_source_and_topic_priority() -> None:
    candidate = Candidate(
        url="https://example.com",
        track="industry",
        topics=["agent"],
        title="Agent update",
        source_kind="company_blog",
        summary="summary",
    )

    scored = score_candidate(candidate, TOPICS_CONFIG)

    assert scored.score == 66
    assert "source:company_blog+12" in scored.score_reasons


def test_score_candidate_can_use_configured_weights() -> None:
    candidate = Candidate(
        url="https://example.com",
        track="industry",
        topics=["agent"],
        title="Agent update",
        source_kind="company_blog",
        summary="summary",
        published="2026-07-07",
    )
    scoring_config = {
        "candidate_scoring": {
            "source_weights": {"company_blog": 20},
            "topic_priority_multiplier": 8,
            "bonuses": {"summary": 3, "published": 1},
        }
    }

    scored = score_candidate(candidate, TOPICS_CONFIG, scoring_config)

    assert scored.score == 64
    assert scored.score_reasons == (
        "source:company_blog+20",
        "topic_priority:5+40",
        "summary+3",
        "published+1",
    )


def test_select_top_candidates_respects_track_quotas_then_fills() -> None:
    candidates = [
        Candidate("https://a.com/1", "academic", ["agent"], "A1", score=100),
        Candidate("https://a.com/2", "academic", ["agent"], "A2", score=90),
        Candidate("https://i.com/1", "industry", ["agent"], "I1", score=80),
        Candidate("https://i.com/2", "industry", ["agent"], "I2", score=70),
    ]

    selected = select_top_candidates(candidates, max_cards=3, academic_quota=1, industry_quota=1)

    assert [candidate.title for candidate in selected] == ["A1", "I1", "A2"]


def test_chinese_media_rss_uses_chinese_media_source_kind() -> None:
    candidate = candidate_from_rss_item(
        RSSItem(
            feed_name="机器之心",
            track="industry",
            title="中文 AI 动态",
            url="https://example.com",
            published="",
            summary="",
        )
    )

    assert candidate.source_kind == "chinese_media"


def test_benchmark_site_uses_benchmark_source_kind() -> None:
    candidate = candidate_from_company_item(
        CompanyBlogItem(
            source_name="Arena.ai",
            track="industry",
            title="Leaderboard changelog",
            url="https://arena.ai/blog/leaderboard-changelog",
        )
    )

    assert candidate.source_kind == "benchmark"


def test_chinese_media_company_item_uses_chinese_media_source_kind() -> None:
    candidate = candidate_from_company_item(
        CompanyBlogItem(
            source_name="量子位",
            track="industry",
            title="中文媒体文章",
            url="https://www.qbitai.com/2026/07/example.html",
        )
    )

    assert candidate.source_kind == "chinese_media"


def test_tencent_research_source_uses_chinese_media_source_kind() -> None:
    candidate = candidate_from_company_item(
        CompanyBlogItem(
            source_name="腾讯研究院",
            track="industry",
            title="腾讯研究院AI速递 20260707",
            url="https://m.sohu.com/a/1046718053_455313",
        )
    )

    assert candidate.source_kind == "chinese_media"


def test_select_top_media_candidates_uses_separate_quota() -> None:
    candidates = [
        Candidate(
            "https://media.example/1",
            "industry",
            ["ai-industry"],
            "M1",
            source_kind="chinese_media",
            score=90,
        ),
        Candidate(
            "https://media.example/2",
            "industry",
            ["ai-industry"],
            "M2",
            source_kind="chinese_media",
            score=80,
        ),
        Candidate(
            "https://official.example/1",
            "industry",
            ["ai-industry"],
            "O1",
            source_kind="company_blog",
            score=100,
        ),
    ]

    selected = select_top_media_candidates(candidates, media_quota=1)

    assert [candidate.title for candidate in selected] == ["M1"]


def test_candidates_for_generation_prioritizes_media_without_changing_selection() -> None:
    candidates = [
        Candidate(
            "https://official.example/1",
            "industry",
            ["ai-industry"],
            "O1",
            source_kind="company_blog",
            score=100,
        ),
        Candidate(
            "https://media.example/1",
            "industry",
            ["ai-industry"],
            "M1",
            source_kind="chinese_media",
            score=90,
        ),
        Candidate(
            "https://official.example/2",
            "industry",
            ["ai-industry"],
            "O2",
            source_kind="company_blog",
            score=80,
        ),
        Candidate(
            "https://media.example/2",
            "industry",
            ["ai-industry"],
            "M2",
            source_kind="chinese_media",
            score=70,
        ),
    ]

    ordered = candidates_for_generation(candidates)

    assert [candidate.title for candidate in ordered] == ["M1", "M2", "O1", "O2"]
    assert [candidate.title for candidate in candidates] == ["O1", "M1", "O2", "M2"]

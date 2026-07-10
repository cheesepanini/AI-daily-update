from fastapi.testclient import TestClient

from ai_daily_update.config import load_settings
from ai_daily_update.feedback.events import read_feedback_events
from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import (
    add_source_topic_option,
    create_app,
    parse_daily_schedule_times,
    trend_group_count,
    trend_term_groups,
    update_source_enabled,
    update_source_topics,
)


def write_test_config(root) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text(
        """
timezone: Asia/Shanghai
storage:
  markdown_root: notes
  sqlite_path: data/kb.sqlite
review:
  statuses:
    - needs-review
    - accepted
    - later
    - rejected
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "sources.yaml").write_text(
        """
sources:
  arxiv:
    enabled: true
    categories: [cs.AI]
  rss:
    enabled: true
    feeds:
      - name: 机器之心
        track: industry
        url: https://www.jiqizhixin.com/rss
  company_blogs:
    enabled: true
    sources:
      - name: Arena.ai
        url: https://arena.ai/blog/
        track: industry
        themes: [benchmark-evaluation]
        include_paths: [/blog/]
      - name: General AI Blog
        url: https://example.com/ai/
        track: industry
        include_paths: [/ai/]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "topics.yaml").write_text(
        """
topics:
  agent:
    name_zh: 智能体
    name_en: AI Agents
    aliases: [agent]
  benchmark-evaluation:
    name_zh: 公开测评与榜单
    name_en: Benchmark Evaluation
    aliases: [leaderboard, benchmark]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_sources_page_filters_by_keyword(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/sources?q=公开测评")

    assert response.status_code == 200
    assert "Arena.ai" in response.text


def test_sources_page_filters_by_theme_and_keeps_general_ai_default(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    benchmark_response = client.get("/sources?theme=benchmark-evaluation")
    general_response = client.get("/sources?theme=general-ai")

    assert benchmark_response.status_code == 200
    assert "Arena.ai" in benchmark_response.text
    assert "General AI Blog" not in benchmark_response.text
    assert "公开测评与榜单" in benchmark_response.text
    assert general_response.status_code == 200
    assert "General AI Blog" in general_response.text
    assert "泛 AI" in general_response.text


def test_update_source_topics_writes_sources_yaml(tmp_path) -> None:
    write_test_config(tmp_path)
    settings = load_settings(tmp_path)

    updated = update_source_topics(settings, "web:1", "agent", "foundation-model")
    reloaded = load_settings(tmp_path)
    source = reloaded.sources["sources"]["company_blogs"]["sources"][1]

    assert updated
    assert source["name"] == "General AI Blog"
    assert source["primary_topic"] == "agent"
    assert source["secondary_topic"] == "foundation-model"
    assert settings.sources["sources"]["company_blogs"]["sources"][1]["primary_topic"] == "agent"


def test_update_source_enabled_writes_sources_yaml(tmp_path) -> None:
    write_test_config(tmp_path)
    settings = load_settings(tmp_path)

    updated = update_source_enabled(settings, "web:1", False)
    reloaded = load_settings(tmp_path)
    source = reloaded.sources["sources"]["company_blogs"]["sources"][1]

    assert updated
    assert source["enabled"] is False
    assert settings.sources["sources"]["company_blogs"]["sources"][1]["enabled"] is False


def test_sources_page_can_update_topics_from_frontend(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/source-themes",
        data={
            "source_key": "web:1",
            "primary_topic": "agent",
            "secondary_topic": "benchmark-evaluation",
            "return_to": "/sources?theme=agent",
        },
        follow_redirects=False,
    )
    filtered = client.get("/sources?theme=agent")

    assert response.status_code == 303
    assert response.headers["location"] == "/sources?theme=agent"
    assert "General AI Blog" in filtered.text
    assert "智能体" in filtered.text


def test_sources_page_can_disable_source_from_frontend(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/source-enabled",
        data={
            "source_key": "web:1",
            "enabled": "false",
            "return_to": "/sources",
        },
        follow_redirects=False,
    )
    page = client.get("/sources")

    assert response.status_code == 303
    assert "停用" in page.text
    events = read_feedback_events(tmp_path)
    assert events[0]["surface"] == "source_subscription"
    assert events[0]["action"] == "disabled"


def test_can_add_source_topic_option(tmp_path) -> None:
    write_test_config(tmp_path)
    settings = load_settings(tmp_path)

    added = add_source_topic_option(settings, "embodied-ai", "具身智能")
    reloaded = load_settings(tmp_path)

    assert added
    assert {"id": "embodied-ai", "label": "具身智能"} in reloaded.sources["sources"][
        "source_topics"
    ]


def test_sources_page_filter_dropdown_includes_unused_custom_topic(tmp_path) -> None:
    write_test_config(tmp_path)
    settings = load_settings(tmp_path)
    add_source_topic_option(settings, "embodied-ai", "具身智能")
    client = TestClient(create_app(tmp_path))

    response = client.get("/sources")

    assert response.status_code == 200
    assert '<option value="embodied-ai"' in response.text
    assert "具身智能" in response.text


def test_trends_page_lists_keyword_counts(tmp_path) -> None:
    write_test_config(tmp_path)
    write_card(
        tmp_path / "notes" / "cards" / "2026" / "07" / "card.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "智能体榜单更新",
            "title_en": "AI Agents leaderboard update",
            "date": "2026-07-07",
            "source_url": "https://arena.ai/blog/",
            "topics": ["benchmark-evaluation"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 一句话结论\n智能体、agent、榜单、leaderboard 和 benchmark 热度上升。",
    )
    client = TestClient(create_app(tmp_path))

    response = client.get("/trends")

    assert response.status_code == 200
    assert "智能体" in response.text
    assert "公开测评与榜单" in response.text
    assert "合并：" in response.text
    assert "AI Agents" in response.text
    assert "leaderboard" in response.text


def test_trend_groups_merge_configured_aliases(tmp_path) -> None:
    write_test_config(tmp_path)
    settings = load_settings(tmp_path)

    groups = trend_term_groups(settings)
    agent_group = next(group for group in groups if group["id"] == "agent")
    benchmark_group = next(group for group in groups if group["id"] == "benchmark-evaluation")

    assert "智能体" in agent_group["terms"]
    assert "AI Agents" in agent_group["terms"]
    assert "agent" in agent_group["terms"]
    assert "榜单" in benchmark_group["terms"]
    assert "leaderboard" in benchmark_group["terms"]
    assert trend_group_count("智能体 agent AI Agents", agent_group["terms"]) == 3


def test_trend_groups_merge_reasoning_terms(tmp_path) -> None:
    write_test_config(tmp_path)
    settings = load_settings(tmp_path)

    groups = trend_term_groups(settings)
    reasoning_group = next(group for group in groups if group["id"] == "reasoning")

    assert reasoning_group["label"] == "推理"
    assert reasoning_group["terms"] == ["推理", "reasoning"]
    assert not any(group["id"] == "推理" for group in groups)
    assert trend_group_count("推理 reasoning", reasoning_group["terms"]) == 2


def test_parse_daily_schedule_times_ignores_invalid_values() -> None:
    parsed = parse_daily_schedule_times(["08:00", "18:00", "25:00", "bad", "8:00", "08:00"])

    assert parsed == [(8, 0), (18, 0)]

from fastapi.testclient import TestClient

from ai_daily_update.config import load_settings
from ai_daily_update.feedback.events import append_feedback_event
from ai_daily_update.preference.features import (
    extract_preference_features,
    read_feature_records,
    safe_int,
)
from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import create_app


def test_safe_int_handles_infinity_without_crashing() -> None:
    assert safe_int(float("inf")) == 0
    assert safe_int(float("-inf")) == 0
    assert safe_int(float("nan")) == 0


def test_extract_preference_features_handles_infinite_score_field(tmp_path) -> None:
    write_test_config(tmp_path)
    write_card(
        tmp_path / "notes" / "cards" / "2026" / "07" / "card.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "测试卡片",
            "date": "2026-07-08",
            "source_url": "https://example.com/a",
            "source_type": "company-news",
            "topics": ["agent"],
            "importance": float("inf"),
            "review_status": "accepted",
        },
        "content",
    )
    settings = load_settings(tmp_path)

    extract_preference_features(settings, surface="cards")
    records = read_feature_records(tmp_path, "cards")

    assert records[0]["features"]["importance"] == 0


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
    (config_dir / "sources.yaml").write_text("sources: {}\n", encoding="utf-8")
    (config_dir / "topics.yaml").write_text("topics: {}\n", encoding="utf-8")


def test_extract_preference_features_writes_card_records_with_labels(tmp_path) -> None:
    write_test_config(tmp_path)
    write_card(
        tmp_path / "notes" / "cards" / "2026" / "07" / "card.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "测试卡片",
            "date": "2026-07-08",
            "source_url": "https://example.com/a",
            "source_type": "company-news",
            "topics": ["agent"],
            "importance": 4,
            "review_status": "accepted",
        },
        "## 一句话结论\n测试。\n\n## 事件概述\n测试。",
    )
    append_feedback_event(
        tmp_path,
        "Asia/Shanghai",
        "card_review",
        "card",
        "card-1",
        "accepted",
        new_status="accepted",
    )
    settings = load_settings(tmp_path)

    paths = extract_preference_features(settings, surface="cards")
    records = read_feature_records(tmp_path, "cards")

    assert paths[0].name == "cards.jsonl"
    assert len(records) == 1
    assert records[0]["entity_id"] == "card-1"
    assert records[0]["label"]["action"] == "accepted"
    assert records[0]["features"]["has_event_overview"] is True


def test_extract_preference_features_writes_source_proposal_records(tmp_path) -> None:
    write_test_config(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "source_proposals.json").write_text(
        """
{
  "generated_at": "2026-07-08T00:00:00+08:00",
  "proposal_version": "v1",
  "proposals": [
    {
      "name": "Example Lab",
      "url": "https://example-lab.ai",
      "primary_topic": "embodied-ai",
      "secondary_topic": "humanoid-robot",
      "reason": "测试",
      "priority": "自动建议",
      "proposal_origin": "accepted-card-domain",
      "score": 70
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    settings = load_settings(tmp_path)

    extract_preference_features(settings, surface="source_proposals")
    records = read_feature_records(tmp_path, "source_proposals")

    assert len(records) == 1
    assert records[0]["features"]["primary_topic"] == "embodied-ai"
    assert records[0]["features"]["score"] == 70


def test_preferences_page_shows_reserved_model_interface(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/preferences")

    assert response.status_code == 200
    assert "偏好学习" in response.text
    assert "模型状态" in response.text
    assert "尚未训练" in response.text

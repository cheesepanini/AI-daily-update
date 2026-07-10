from fastapi.testclient import TestClient

from ai_daily_update.storage import db
from ai_daily_update.storage.markdown import read_card, write_card
from ai_daily_update.web import create_app


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


def test_card_event_date_action_updates_metadata_and_index(tmp_path) -> None:
    write_test_config(tmp_path)
    card_path = tmp_path / "notes" / "cards" / "2026" / "07" / "card.md"
    write_card(
        card_path,
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "测试卡片",
            "date": "2026-07-08",
            "collected_date": "2026-07-08",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 事件概述\n2026 年 6 月 4 日，测试事件发生。",
    )
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/card-event-date",
        data={
            "card_id": "card-1",
            "event_date": "2026-06-04",
            "return_to": "/cards/card-1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/cards/card-1"
    assert read_card(card_path).metadata["event_date"] == "2026-06-04"

    connection = db.connect(tmp_path / "data" / "kb.sqlite")
    rows = db.query_cards(
        connection, "2026-06-04", "2026-06-04", None, "industry", date_basis="event"
    )
    assert [row["id"] for row in rows] == ["card-1"]


def test_card_event_date_action_ignores_invalid_date(tmp_path) -> None:
    write_test_config(tmp_path)
    card_path = tmp_path / "notes" / "cards" / "2026" / "07" / "card.md"
    write_card(
        card_path,
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "测试卡片",
            "date": "2026-07-08",
            "event_date": "2026-07-01",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/card-event-date",
        data={"card_id": "card-1", "event_date": "not-a-date", "return_to": "/cards"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert read_card(card_path).metadata["event_date"] == "2026-07-01"

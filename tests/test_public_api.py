from fastapi.testclient import TestClient

from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import create_app


def write_test_config(root) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "app.yaml").write_text(
        """
timezone: Asia/Shanghai
auth:
  enabled: true
  username: admin
  password: secret
  session_secret: test-secret
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


def write_api_card(
    root,
    card_id: str,
    status: str,
    date: str,
    event_date: str,
    track: str = "industry",
    topics: list[str] | None = None,
) -> None:
    write_card(
        root / "notes" / "cards" / "2026" / "07" / f"{card_id}.md",
        {
            "id": card_id,
            "track": track,
            "title_zh": f"标题 {card_id}",
            "title_en": f"Title {card_id}",
            "date": date,
            "event_date": event_date,
            "collected_date": date,
            "source_url": f"https://example.com/{card_id}",
            "topics": topics or ["ai-industry"],
            "entities": [],
            "review_status": status,
        },
        "## 一句话结论\n这是一条结论。\n\n## 事件概述\n这是一条事件概述。",
    )


def test_public_api_lists_cards_without_login_and_sorts_by_event_date(tmp_path) -> None:
    write_test_config(tmp_path)
    write_api_card(tmp_path, "old", "accepted", "2026-07-08", "2026-06-04")
    write_api_card(tmp_path, "new", "needs-review", "2026-07-07", "2026-07-07")
    write_api_card(tmp_path, "later", "later", "2026-07-06", "2026-07-01")
    write_api_card(tmp_path, "hidden", "rejected", "2026-07-09", "2026-07-09")
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/v1/cards?page=1&page_size=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "v1"
    assert payload["pagination"]["total"] == 3
    assert [item["id"] for item in payload["items"]] == ["new", "later"]


def test_public_api_filters_cards(tmp_path) -> None:
    write_test_config(tmp_path)
    write_api_card(
        tmp_path,
        "agent",
        "accepted",
        "2026-07-08",
        "2026-07-08",
        topics=["agent"],
    )
    write_api_card(
        tmp_path,
        "academic",
        "accepted",
        "2026-07-06",
        "2026-07-06",
        track="academic",
        topics=["foundation-model"],
    )
    client = TestClient(create_app(tmp_path))

    topic_response = client.get("/api/v1/cards?topic=agent")
    track_response = client.get("/api/v1/cards?track=academic")
    date_response = client.get("/api/v1/cards?from_date=2026-07-07&to_date=2026-07-09")

    assert [item["id"] for item in topic_response.json()["items"]] == ["agent"]
    assert [item["id"] for item in track_response.json()["items"]] == ["academic"]
    assert [item["id"] for item in date_response.json()["items"]] == ["agent"]


def test_public_api_card_detail_returns_sections_and_hides_rejected(tmp_path) -> None:
    write_test_config(tmp_path)
    write_api_card(tmp_path, "visible", "accepted", "2026-07-08", "2026-07-08")
    write_api_card(tmp_path, "hidden", "rejected", "2026-07-08", "2026-07-08")
    client = TestClient(create_app(tmp_path))

    detail = client.get("/api/v1/cards/visible")
    hidden = client.get("/api/v1/cards/hidden")

    assert detail.status_code == 200
    assert detail.json()["id"] == "visible"
    assert detail.json()["sections"][0]["title"] == "一句话结论"
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"


def test_public_api_meta_is_public(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    assert response.json()["api_version"] == "v1"
    assert response.json()["default_page_size"] == 20

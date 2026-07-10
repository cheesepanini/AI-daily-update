from fastapi.testclient import TestClient

from ai_daily_update.storage.markdown import write_card
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


def write_numbered_card(root, index: int, status: str = "needs-review") -> None:
    write_card(
        root / "notes" / "cards" / "2026" / "07" / f"card-{index:02d}.md",
        {
            "id": f"card-{index:02d}",
            "track": "industry",
            "title_zh": f"卡片 {index:02d}",
            "title_en": f"Card {index:02d}",
            "date": f"2026-07-{index:02d}" if index <= 25 else "2026-07-01",
            "source_url": f"https://example.com/{index}",
            "topics": [],
            "entities": [],
            "review_status": status,
        },
        "## 一句话结论\n分页测试。",
    )


def test_cards_page_shows_recent_twenty_by_default(tmp_path) -> None:
    write_test_config(tmp_path)
    for index in range(1, 26):
        write_numbered_card(tmp_path, index)
    client = TestClient(create_app(tmp_path))

    response = client.get("/cards")

    assert response.status_code == 200
    assert "显示第 1-20 条，共 25 条" in response.text
    assert "卡片 25" in response.text
    assert "卡片 06" in response.text
    assert "卡片 05" not in response.text
    assert "href=\"/cards?page=2\"" in response.text


def test_dashboard_renders_review_queue_when_cards_exist(tmp_path) -> None:
    write_test_config(tmp_path)
    write_numbered_card(tmp_path, 1, status="needs-review")
    client = TestClient(create_app(tmp_path))

    response = client.get("/")

    assert response.status_code == 200
    assert "审核队列" in response.text
    assert 'data-card-id="card-01"' in response.text


def test_cards_page_second_page_preserves_filters(tmp_path) -> None:
    write_test_config(tmp_path)
    for index in range(1, 26):
        write_numbered_card(tmp_path, index)
    client = TestClient(create_app(tmp_path))

    response = client.get("/cards?status=needs-review&track=industry&page=2")

    assert response.status_code == 200
    assert "显示第 21-25 条，共 25 条" in response.text
    assert "卡片 05" in response.text
    assert "卡片 06" not in response.text
    assert "href=\"/cards?status=needs-review&amp;track=industry\"" in response.text


def test_cards_page_allows_revising_accepted_and_rejected_statuses(tmp_path) -> None:
    write_test_config(tmp_path)
    write_numbered_card(tmp_path, 1, status="accepted")
    write_numbered_card(tmp_path, 2, status="rejected")
    client = TestClient(create_app(tmp_path))

    accepted_page = client.get("/cards?status=accepted")
    rejected_page = client.get("/cards?status=rejected")

    assert accepted_page.status_code == 200
    assert 'name="status" value="needs-review"' in accepted_page.text
    assert 'name="status" value="rejected"' in accepted_page.text
    assert "删除" in accepted_page.text
    assert rejected_page.status_code == 200
    assert 'name="status" value="accepted"' in rejected_page.text
    assert 'name="status" value="needs-review"' in rejected_page.text


def test_review_action_returns_json_for_fetch_requests(tmp_path) -> None:
    write_test_config(tmp_path)
    write_numbered_card(tmp_path, 1, status="needs-review")
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/review",
        data={
            "card_id": "card-01",
            "status": "accepted",
            "return_to": "/cards",
        },
        headers={"X-Requested-With": "fetch", "Accept": "application/json"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["status"] == "accepted"
    assert payload["status_label"] == "已接受"
    assert 'data-card-status-actions' in payload["actions_html"]
    assert 'name="status" value="rejected"' in payload["actions_html"]

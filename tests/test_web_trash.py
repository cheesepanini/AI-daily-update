from fastapi.testclient import TestClient

from ai_daily_update.storage.markdown import read_card, write_card
from ai_daily_update.web import create_app, move_card_to_trash
from ai_daily_update.config import load_settings


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


def test_trash_page_lists_deleted_cards(tmp_path) -> None:
    write_test_config(tmp_path)
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "trash" / "2026" / "07" / "deleted.md",
        {
            "id": "deleted-1",
            "track": "industry",
            "title_zh": "已删除卡片",
            "date": "2026-07-07",
            "deleted_at": "2026-07-07T10:00:00+08:00",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 事件概述\n已删除内容。",
    )
    client = TestClient(create_app(tmp_path))

    response = client.get("/trash")

    assert response.status_code == 200
    assert "回收站" in response.text
    assert "已删除卡片" in response.text
    assert "2026-07-07T10:00:00+08:00" in response.text


def test_move_card_to_trash_records_deleted_at(tmp_path) -> None:
    write_test_config(tmp_path)
    markdown_root = tmp_path / "notes"
    path = markdown_root / "cards" / "2026" / "07" / "card.md"
    write_card(
        path,
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "卡片",
            "date": "2026-07-07",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    settings = load_settings(tmp_path)

    target = move_card_to_trash(settings, path)

    assert not path.exists()
    assert target.exists()
    assert read_card(target).metadata["deleted_at"]

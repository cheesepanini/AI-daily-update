from fastapi.testclient import TestClient

from ai_daily_update.storage.indexer import rebuild_index
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


def test_briefs_page_renders(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/briefs")

    assert response.status_code == 200
    assert "简报生成" in response.text
    assert "本日简报" in response.text
    assert "本周简报" in response.text
    assert "自定义时间段" in response.text


def test_brief_action_generates_markdown_from_accepted_cards(tmp_path) -> None:
    write_test_config(tmp_path)
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "07" / "accepted.md",
        {
            "id": "accepted-1",
            "track": "academic",
            "title_zh": "测试论文",
            "title_en": "Test Paper",
            "date": "2026-07-07",
            "source_url": "https://arxiv.org/abs/2607.00001",
            "topics": ["foundation-model"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    rebuild_index(markdown_root, tmp_path / "data" / "kb.sqlite")
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/brief",
        data={
            "preset": "custom",
            "from_date": "2026-07-07",
            "to_date": "2026-07-07",
            "audience": "academic",
            "topics": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    brief_path = markdown_root / "briefs" / "academic" / "2026-07-07_to_2026-07-07_collected_all.md"
    assert brief_path.exists()
    assert "测试论文" in brief_path.read_text(encoding="utf-8")

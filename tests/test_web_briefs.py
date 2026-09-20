import os

from fastapi.testclient import TestClient

from ai_daily_update.storage.indexer import rebuild_index
from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import brief_id_for_relative_path, create_app


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
    assert "每日简报" in response.text
    assert "每周简报" in response.text
    assert "自定义时间段" in response.text
    assert 'data-brief-form' in response.text
    assert 'data-from-date' in response.text
    assert 'id="brief-job-panel"' in response.text
    assert '/actions/delete-brief' not in response.text


def test_briefs_page_hides_generated_file_name_and_path(tmp_path) -> None:
    write_test_config(tmp_path)
    brief_path = tmp_path / "notes" / "briefs" / "academic" / "2026-07-07_to_2026-07-07_collected_all.md"
    brief_path.parent.mkdir(parents=True)
    brief_path.write_text("# 测试简报\n\n正文", encoding="utf-8")

    response = TestClient(create_app(tmp_path)).get("/briefs")

    assert response.status_code == 200
    assert "测试简报" in response.text
    assert brief_path.name not in response.text
    assert str(brief_path) not in response.text
    assert ">删除<" in response.text
    assert '<details class="brief-details">' in response.text
    assert 'class="brief-expand-label"' in response.text


def test_briefs_are_ordered_by_generation_time_and_can_be_deleted(tmp_path) -> None:
    write_test_config(tmp_path)
    briefs_root = tmp_path / "notes" / "briefs" / "academic"
    older = briefs_root / "z-old.md"
    newer = briefs_root / "a-new.md"
    briefs_root.mkdir(parents=True)
    older.write_text("# 较早生成的简报", encoding="utf-8")
    newer.write_text("# 最新生成的简报", encoding="utf-8")
    os.utime(older, ns=(1_000_000_000, 1_000_000_000))
    os.utime(newer, ns=(2_000_000_000, 2_000_000_000))
    client = TestClient(create_app(tmp_path))

    response = client.get("/briefs")

    assert response.text.index("最新生成的简报") < response.text.index("较早生成的简报")
    brief_id = brief_id_for_relative_path("academic/a-new.md")
    deleted = client.post("/actions/delete-brief", data={"brief_id": brief_id}, follow_redirects=False)

    assert deleted.status_code == 303
    assert not newer.exists()
    assert older.exists()


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


def test_brief_action_starts_background_job_for_fetch_request(tmp_path) -> None:
    write_test_config(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/actions/brief",
        data={"preset": "today", "audience": "academic"},
        headers={"X-Requested-With": "fetch"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["job"]["job_type"] == "brief"
    assert payload["job"]["label"] == "生成简报"

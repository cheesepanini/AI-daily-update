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
    (config_dir / "topics.yaml").write_text(
        """
topics:
  foundation-model:
    name_zh: 预训练大模型
    priority: 5
    aliases: [foundation model]
  agent:
    name_zh: 智能体
    priority: 3
    aliases: [AI agent]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def write_topic_card(
    root, card_id: str, title_zh: str, topics: list[str], status: str = "accepted"
) -> None:
    write_card(
        root / "notes" / "cards" / "2026" / "07" / f"{card_id}.md",
        {
            "id": card_id,
            "track": "industry",
            "title_zh": title_zh,
            "title_en": title_zh,
            "date": "2026-07-07",
            "source_url": "https://example.com",
            "topics": topics,
            "entities": [],
            "review_status": status,
        },
        f"## 一句话结论\n{title_zh} 的结论内容。",
    )


def test_cards_page_filters_by_topic(tmp_path) -> None:
    write_test_config(tmp_path)
    write_topic_card(tmp_path, "card-fm", "多模态大模型进展", ["foundation-model"])
    write_topic_card(tmp_path, "card-agent", "智能体框架发布", ["agent"])
    client = TestClient(create_app(tmp_path))

    response = client.get("/cards?topic=foundation-model")

    assert response.status_code == 200
    assert "多模态大模型进展" in response.text
    assert "智能体框架发布" not in response.text
    assert "预训练大模型" in response.text
    assert "智能体" in response.text


def test_cards_page_filters_by_keyword(tmp_path) -> None:
    write_test_config(tmp_path)
    write_topic_card(tmp_path, "card-fm", "多模态大模型进展", ["foundation-model"])
    write_topic_card(tmp_path, "card-agent", "智能体框架发布", ["agent"])
    client = TestClient(create_app(tmp_path))

    response = client.get("/cards?q=智能体")

    assert response.status_code == 200
    assert "智能体框架发布" in response.text
    assert "多模态大模型进展" not in response.text


def test_public_page_filters_by_topic_and_keyword(tmp_path) -> None:
    write_test_config(tmp_path)
    write_topic_card(tmp_path, "card-fm", "多模态大模型进展", ["foundation-model"])
    write_topic_card(tmp_path, "card-agent", "智能体框架发布", ["agent"])
    client = TestClient(create_app(tmp_path))

    by_topic = client.get("/public?topic=agent")
    by_keyword = client.get("/public?q=多模态")

    assert by_topic.status_code == 200
    assert "智能体框架发布" in by_topic.text
    assert "多模态大模型进展" not in by_topic.text

    assert by_keyword.status_code == 200
    assert "多模态大模型进展" in by_keyword.text
    assert "智能体框架发布" not in by_keyword.text

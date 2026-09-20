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
    (config_dir / "foundational_concepts.yaml").write_text(
        """
category_labels:
  neural-networks: 神经网络与深度学习

concepts:
  transformer-attention:
    name_zh: Transformer 与注意力机制
    name_en: Transformer & Attention Mechanism
    category: neural-networks
    aliases:
      - transformer
    applies_to_topics: [foundation-model]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def write_test_card(root) -> None:
    write_card(
        root / "notes" / "cards" / "2026" / "07" / "card-1.md",
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "某公司发布新的 Transformer 模型",
            "title_en": "",
            "date": "2026-07-08",
            "collected_date": "2026-07-08",
            "source_url": "https://example.com/card-1",
            "topics": ["foundation-model"],
            "entities": [],
            "review_status": "accepted",
        },
        "## 一句话结论\n某公司发布了新的模型。\n",
    )


def test_card_detail_shows_matched_foundational_concepts(tmp_path) -> None:
    write_test_config(tmp_path)
    write_test_card(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/cards/card-1")

    assert response.status_code == 200
    assert "Transformer 与注意力机制" in response.text


def test_public_card_detail_shows_matched_foundational_concepts(tmp_path) -> None:
    write_test_config(tmp_path)
    write_test_card(tmp_path)
    client = TestClient(create_app(tmp_path))

    response = client.get("/public/cards/card-1")

    assert response.status_code == 200
    assert "Transformer 与注意力机制" in response.text

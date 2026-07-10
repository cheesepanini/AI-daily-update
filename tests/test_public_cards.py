from ai_daily_update.config import load_settings
from ai_daily_update.storage.markdown import write_card
from ai_daily_update.web import public_cards


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


def write_public_card(root, card_id: str, status: str, date: str, event_date: str = "") -> None:
    metadata = {
        "id": card_id,
        "track": "industry",
        "title_zh": card_id,
        "date": date,
        "source_url": f"https://example.com/{card_id}",
        "topics": ["ai-industry"],
        "entities": [],
        "review_status": status,
    }
    if event_date:
        metadata["event_date"] = event_date
    write_card(
        root / "notes" / "cards" / "2026" / "07" / f"{card_id}.md",
        metadata,
        "## 一句话结论\n测试。",
    )


def test_public_cards_include_reviewable_cards_and_sort_by_event_date(tmp_path) -> None:
    write_test_config(tmp_path)
    write_public_card(tmp_path, "accepted-old", "accepted", "2026-07-08", "2026-06-04")
    write_public_card(tmp_path, "needs-review-new", "needs-review", "2026-07-07", "2026-07-07")
    write_public_card(tmp_path, "later-mid", "later", "2026-07-01", "2026-07-01")
    write_public_card(tmp_path, "rejected-hidden", "rejected", "2026-07-09", "2026-07-09")
    settings = load_settings(tmp_path)

    cards = public_cards(settings)

    assert [card["id"] for card in cards] == ["needs-review-new", "later-mid", "accepted-old"]
    assert [card["event_date"] for card in cards] == ["2026-07-07", "2026-07-01", "2026-06-04"]

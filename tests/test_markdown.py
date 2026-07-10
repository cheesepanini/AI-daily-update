from ai_daily_update.storage.markdown import read_card, update_metadata, write_card


def test_write_read_and_update_card(tmp_path) -> None:
    path = tmp_path / "card.md"
    write_card(
        path,
        {"id": "card-1", "review_status": "needs-review", "topics": ["agent"]},
        "## 一句话结论\n\n内容。\n",
    )

    card = read_card(path)
    assert card.metadata["id"] == "card-1"
    assert "一句话结论" in card.content

    updated = update_metadata(path, {"review_status": "accepted"})
    assert updated.metadata["review_status"] == "accepted"

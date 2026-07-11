import threading

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


def test_concurrent_update_metadata_calls_do_not_clobber_each_other(tmp_path) -> None:
    path = tmp_path / "card.md"
    write_card(
        path,
        {"id": "card-1", "review_status": "needs-review"},
        "content",
    )

    # Simulate two independent callers racing on the same card, each setting
    # a *different* field (e.g. a manual review action setting review_status
    # while a delete action sets deleted_at). Each is a plain read-modify-
    # write of the whole file, so without a lock the second writer's fresh
    # read overwrites the first writer's change with the pre-update value.
    def set_review_status() -> None:
        for _ in range(20):
            update_metadata(path, {"review_status": "accepted"})

    def set_deleted_at() -> None:
        for i in range(20):
            update_metadata(path, {"deleted_at": f"2026-07-08T00:00:{i:02d}"})

    threads = [
        threading.Thread(target=set_review_status),
        threading.Thread(target=set_deleted_at),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final = read_card(path)
    assert final.metadata["review_status"] == "accepted"
    assert final.metadata["deleted_at"] == "2026-07-08T00:00:19"

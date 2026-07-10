from ai_daily_update.cli import clean_llm_markdown, existing_card_source_urls
from ai_daily_update.processors.dedupe import normalize_url_for_dedupe
from ai_daily_update.storage.markdown import write_card


def test_clean_llm_markdown_removes_outer_fence() -> None:
    assert clean_llm_markdown("```markdown\n# Title\n\nBody\n```") == "# Title\n\nBody\n"


def test_existing_card_source_urls_includes_trash(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "07" / "active.md",
        {
            "id": "active",
            "track": "industry",
            "date": "2026-07-07",
            "source_url": "https://example.com/active?utm_source=test",
            "topics": [],
            "entities": [],
        },
        "content",
    )
    write_card(
        markdown_root / "trash" / "2026" / "07" / "deleted.md",
        {
            "id": "deleted",
            "track": "industry",
            "date": "2026-07-07",
            "source_url": "https://example.com/deleted?utm_source=test",
            "topics": [],
            "entities": [],
        },
        "content",
    )

    urls = existing_card_source_urls(markdown_root)

    assert normalize_url_for_dedupe("https://example.com/active") in urls
    assert normalize_url_for_dedupe("https://example.com/deleted") in urls

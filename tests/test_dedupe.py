from dataclasses import dataclass

from ai_daily_update.processors.dedupe import (
    dedupe_items,
    normalize_title_for_dedupe,
    normalize_url_for_dedupe,
)


@dataclass(frozen=True)
class Item:
    url: str
    title: str


def test_normalize_url_removes_tracking_and_fragment() -> None:
    assert (
        normalize_url_for_dedupe("https://www.example.com/post/?utm_source=x&keep=1#section")
        == "https://example.com/post?keep=1"
    )


def test_normalize_url_unifies_arxiv_pdf_and_abs() -> None:
    assert (
        normalize_url_for_dedupe("https://arxiv.org/pdf/1706.03762.pdf")
        == "https://arxiv.org/abs/1706.03762"
    )


def test_normalize_title_collapses_case_and_whitespace() -> None:
    assert normalize_title_for_dedupe("  New   Agent Platform ") == "new agent platform"


def test_dedupe_items_filters_duplicate_url_or_title() -> None:
    items = [
        Item("https://example.com/a?utm_source=x", "First"),
        Item("https://example.com/a", "Different title"),
        Item("https://example.com/b", "First"),
        Item("https://example.com/c", "Third"),
    ]

    result = dedupe_items(items)

    assert result.unique == [items[0], items[3]]
    assert result.duplicates == [items[1], items[2]]

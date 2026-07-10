from ai_daily_update.storage.indexer import rebuild_index
from ai_daily_update.storage import db
from ai_daily_update.storage.markdown import write_card


def test_rebuild_index_indexes_cards(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    card_path = markdown_root / "cards" / "2026" / "07" / "card.md"
    write_card(
        card_path,
        {
            "id": "card-1",
            "track": "industry",
            "title_zh": "标题",
            "date": "2026-07-06",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": ["example.com"],
            "review_status": "accepted",
        },
        "content",
    )

    indexed, warnings = rebuild_index(markdown_root, tmp_path / "data" / "kb.sqlite")

    assert indexed == 1
    assert warnings == []


def test_query_cards_filters_academic_and_industry_audience(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "07" / "academic.md",
        {
            "id": "academic-1",
            "track": "academic",
            "title_zh": "学术",
            "date": "2026-07-06",
            "source_url": "https://arxiv.org",
            "topics": ["foundation-model"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    write_card(
        markdown_root / "cards" / "2026" / "07" / "industry.md",
        {
            "id": "industry-1",
            "track": "industry",
            "title_zh": "产业",
            "date": "2026-07-06",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    sqlite_path = tmp_path / "data" / "kb.sqlite"
    rebuild_index(markdown_root, sqlite_path)
    connection = db.connect(sqlite_path)

    academic_rows = db.query_cards(connection, "2026-07-01", "2026-07-31", None, "academic")
    industry_rows = db.query_cards(connection, "2026-07-01", "2026-07-31", None, "industry")

    assert [row["id"] for row in academic_rows] == ["academic-1"]
    assert [row["id"] for row in industry_rows] == ["industry-1"]


def test_query_cards_can_filter_by_collected_date(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "06" / "industry.md",
        {
            "id": "industry-1",
            "track": "industry",
            "title_zh": "产业",
            "date": "2026-06-23",
            "collected_date": "2026-07-07",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    sqlite_path = tmp_path / "data" / "kb.sqlite"
    rebuild_index(markdown_root, sqlite_path)
    connection = db.connect(sqlite_path)

    event_rows = db.query_cards(
        connection, "2026-07-07", "2026-07-07", None, "industry", date_basis="event"
    )
    collected_rows = db.query_cards(
        connection, "2026-07-07", "2026-07-07", None, "industry", date_basis="collected"
    )

    assert event_rows == []
    assert [row["id"] for row in collected_rows] == ["industry-1"]


def test_query_cards_event_basis_prefers_event_date(tmp_path) -> None:
    markdown_root = tmp_path / "notes"
    write_card(
        markdown_root / "cards" / "2026" / "07" / "industry.md",
        {
            "id": "industry-1",
            "track": "industry",
            "title_zh": "产业",
            "date": "2026-07-08",
            "event_date": "2026-06-04",
            "collected_date": "2026-07-08",
            "source_url": "https://example.com",
            "topics": ["ai-industry"],
            "entities": [],
            "review_status": "accepted",
        },
        "content",
    )
    sqlite_path = tmp_path / "data" / "kb.sqlite"
    rebuild_index(markdown_root, sqlite_path)
    connection = db.connect(sqlite_path)

    event_rows = db.query_cards(
        connection, "2026-06-04", "2026-06-04", None, "industry", date_basis="event"
    )
    info_date_rows = db.query_cards(
        connection, "2026-07-08", "2026-07-08", None, "industry", date_basis="event"
    )
    collected_rows = db.query_cards(
        connection, "2026-07-08", "2026-07-08", None, "industry", date_basis="collected"
    )

    assert [row["id"] for row in event_rows] == ["industry-1"]
    assert info_date_rows == []
    assert [row["id"] for row in collected_rows] == ["industry-1"]

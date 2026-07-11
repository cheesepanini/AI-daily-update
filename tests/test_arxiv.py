from datetime import date

import pytest

from ai_daily_update.collectors.arxiv import (
    build_arxiv_search_query,
    extract_arxiv_id,
    parse_arxiv_atom,
    parse_arxiv_feed,
)


ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <updated>2023-08-02T00:00:00Z</updated>
    <published>2017-06-12T00:00:00Z</published>
    <title>Attention Is All You Need</title>
    <summary>
      The dominant sequence transduction models are based on complex recurrent
      or convolutional neural networks.
    </summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.LG"/>
  </entry>
</feed>
"""


def test_extract_arxiv_id_from_abs_and_pdf_urls() -> None:
    assert extract_arxiv_id("https://arxiv.org/abs/1706.03762") == "1706.03762"
    assert extract_arxiv_id("https://arxiv.org/pdf/1706.03762.pdf") == "1706.03762"
    assert extract_arxiv_id("1706.03762v7") == "1706.03762v7"


def test_parse_arxiv_atom_builds_source_document() -> None:
    document = parse_arxiv_atom(ARXIV_XML, requested_id="1706.03762")

    assert document.title == "Attention Is All You Need"
    assert document.url == "https://arxiv.org/abs/1706.03762"
    assert "Authors: Ashish Vaswani, Noam Shazeer" in document.text
    assert "Primary category: cs.CL" in document.text
    assert "Abstract:" in document.text


def test_build_arxiv_search_query_rejects_empty_categories() -> None:
    with pytest.raises(ValueError):
        build_arxiv_search_query([])
    with pytest.raises(ValueError):
        build_arxiv_search_query(["", "  "])


def test_build_arxiv_search_query_skips_blank_categories() -> None:
    query = build_arxiv_search_query(["cs.AI", "", "cs.CL"])

    assert query == "(cat:cs.AI OR cat:cs.CL)"


def test_build_arxiv_search_query_supports_categories_and_date_range() -> None:
    query = build_arxiv_search_query(
        ["cs.AI", "cs.CL"],
        from_date=date(2026, 7, 1),
        to_date=date(2026, 7, 6),
    )

    assert query == (
        "(cat:cs.AI OR cat:cs.CL) AND "
        "submittedDate:[202607010000 TO 202607062359]"
    )


def test_parse_arxiv_feed_returns_all_entries() -> None:
    documents = parse_arxiv_feed(ARXIV_XML)

    assert len(documents) == 1
    assert documents[0].url == "https://arxiv.org/abs/1706.03762v7"

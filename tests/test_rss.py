from ai_daily_update.collectors.rss import RSSFeedConfig, feeds_from_settings, parse_rss_feed


RSS_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <item>
      <title>First Item</title>
      <link>https://example.com/first</link>
      <pubDate>Mon, 06 Jul 2026 10:00:00 GMT</pubDate>
      <description>First summary.</description>
    </item>
    <item>
      <title>Second Item</title>
      <link>https://example.com/second</link>
      <description>Second summary.</description>
    </item>
  </channel>
</rss>
"""


def test_parse_rss_feed_returns_items() -> None:
    feed = RSSFeedConfig(name="Example", track="industry", url="https://example.com/rss")

    items = parse_rss_feed(RSS_XML, feed)

    assert len(items) == 2
    assert items[0].feed_name == "Example"
    assert items[0].track == "industry"
    assert items[0].title == "First Item"
    assert items[0].url == "https://example.com/first"
    assert items[0].published == "Mon, 06 Jul 2026 10:00:00 GMT"


def test_parse_rss_feed_filters_by_include_keywords() -> None:
    feed = RSSFeedConfig(
        name="Science",
        track="academic",
        url="https://example.com/rss",
        include_keywords=("machine learning", "robotics"),
    )

    items = parse_rss_feed(RSS_XML, feed)

    assert items == []

    matching_xml = RSS_XML.replace("Second summary.", "A machine learning result.")
    items = parse_rss_feed(matching_xml, feed)

    assert [item.title for item in items] == ["Second Item"]


def test_feeds_from_settings_reads_configured_feeds() -> None:
    settings = {
        "sources": {
            "rss": {
                "feeds": [
                    {
                        "name": "OpenAI News",
                        "track": "industry",
                        "url": "https://openai.com/news/rss.xml",
                    }
                ]
            }
        }
    }

    feeds = feeds_from_settings(settings)

    assert feeds == [
        RSSFeedConfig(
            name="OpenAI News",
            track="industry",
            url="https://openai.com/news/rss.xml",
        )
    ]


def test_feeds_from_settings_skips_disabled_feeds() -> None:
    settings = {
        "sources": {
            "rss": {
                "feeds": [
                    {
                        "name": "Disabled",
                        "track": "industry",
                        "url": "https://example.com/rss.xml",
                        "enabled": False,
                    }
                ]
            }
        }
    }

    assert feeds_from_settings(settings) == []


def test_feeds_from_settings_reads_include_keywords() -> None:
    settings = {
        "sources": {
            "rss": {
                "feeds": [
                    {
                        "name": "Nature",
                        "track": "academic",
                        "url": "https://www.nature.com/nature.rss",
                        "include_keywords": ["machine learning", "robotics"],
                    }
                ]
            }
        }
    }

    feeds = feeds_from_settings(settings)

    assert feeds[0].include_keywords == ("machine learning", "robotics")

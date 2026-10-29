from __future__ import annotations

import json
from datetime import datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo


def render_feed(items: list[dict[str, str]], title: str, home: str, feed_url: str, kind: str, timezone: str) -> tuple[str, str]:
    def published(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo(timezone))

    def xml(value: str) -> str:
        return escape("".join(char for char in value if ord(char) in (9, 10, 13) or ord(char) >= 32))

    if kind == "json":
        return json.dumps({"version": "https://jsonfeed.org/version/1.1", "title": title,
                           "home_page_url": home, "feed_url": feed_url,
                           "items": [{"id": item["url"], "url": item["url"], "title": item["title"],
                                      "content_text": item["summary"], "date_published": published(item["date"]).isoformat()}
                                     for item in items]}, ensure_ascii=False), "application/feed+json; charset=utf-8"
    entries = []
    for item in items:
        entries.append(f"<item><title>{xml(item['title'])}</title><link>{xml(item['url'])}</link>"
                       f"<guid isPermaLink=\"true\">{xml(item['url'])}</guid>"
                       f"<description>{xml(item['summary'])}</description>"
                       f"<pubDate>{format_datetime(published(item['date']))}</pubDate></item>")
    return ("<?xml version=\"1.0\" encoding=\"utf-8\"?><rss version=\"2.0\"><channel>"
            f"<title>{xml(title)}</title><link>{xml(home)}</link>"
            f"<description>{xml(title)}</description>" + "".join(entries) + "</channel></rss>",
            "application/rss+xml; charset=utf-8")

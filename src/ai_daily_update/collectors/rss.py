from __future__ import annotations

from dataclasses import dataclass

import feedparser
import requests

from ai_daily_update.collectors.document import normalize_text


@dataclass(frozen=True)
class RSSFeedConfig:
    name: str
    track: str
    url: str
    include_keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class RSSItem:
    feed_name: str
    track: str
    title: str
    url: str
    published: str
    summary: str


def feeds_from_settings(settings: dict) -> list[RSSFeedConfig]:
    feed_configs = settings.get("sources", {}).get("rss", {}).get("feeds", [])
    return [
        RSSFeedConfig(
            name=item.get("name", item.get("url", "RSS Feed")),
            track=item.get("track", "industry"),
            url=item["url"],
            include_keywords=tuple(item.get("include_keywords", []) or []),
        )
        for item in feed_configs
        if item.get("url") and item.get("enabled", True) is not False
    ]


def fetch_rss_feed(feed: RSSFeedConfig, timeout: int = 20) -> list[RSSItem]:
    response = requests.get(
        feed.url,
        timeout=timeout,
        headers={"User-Agent": "AI-Daily-Update/0.1 (local knowledge base)"},
    )
    response.raise_for_status()
    return parse_rss_feed(response.text, feed)


def parse_rss_feed(xml_text: str, feed: RSSFeedConfig) -> list[RSSItem]:
    parsed = feedparser.parse(xml_text)
    items: list[RSSItem] = []
    for entry in parsed.entries:
        url = entry.get("link", "")
        title = normalize_text(entry.get("title", ""))
        if not url or not title:
            continue
        summary = normalize_text(
            entry.get("summary", "") or entry.get("description", "")
        )
        if feed.include_keywords and not matches_include_keywords(
            f"{title}\n{summary}", feed.include_keywords
        ):
            continue
        published = (
            entry.get("published", "")
            or entry.get("updated", "")
            or entry.get("created", "")
        )
        items.append(
            RSSItem(
                feed_name=feed.name,
                track=feed.track,
                title=title,
                url=url,
                published=published,
                summary=summary,
            )
        )
    return items


def fetch_all_rss_feeds(
    feeds: list[RSSFeedConfig], max_per_feed: int = 5, timeout: int = 8
) -> tuple[list[RSSItem], list[str]]:
    items: list[RSSItem] = []
    warnings: list[str] = []
    for feed in feeds:
        try:
            feed_items = fetch_rss_feed(feed, timeout=timeout)
        except Exception as exc:
            warnings.append(f"{feed.name}: {exc}")
            continue
        items.extend(feed_items[:max_per_feed])
    return items, warnings


def matches_include_keywords(text: str, keywords: tuple[str, ...]) -> bool:
    normalized = text.lower()
    return any(keyword.lower() in normalized for keyword in keywords if keyword.strip())

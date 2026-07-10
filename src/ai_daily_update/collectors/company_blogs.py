from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from ai_daily_update.collectors.document import normalize_text


@dataclass(frozen=True)
class CompanyBlogConfig:
    name: str
    url: str
    track: str = "industry"
    include_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompanyBlogItem:
    source_name: str
    track: str
    title: str
    url: str


def company_blogs_from_settings(settings: dict) -> list[CompanyBlogConfig]:
    raw_sources = settings.get("sources", {}).get("company_blogs", {}).get("sources", [])
    default_track = settings.get("sources", {}).get("company_blogs", {}).get("track", "industry")
    sources: list[CompanyBlogConfig] = []
    for item in raw_sources:
        if isinstance(item, str):
            continue
        if not item.get("url"):
            continue
        if item.get("enabled", True) is False:
            continue
        sources.append(
            CompanyBlogConfig(
                name=item.get("name", item["url"]),
                url=item["url"],
                track=item.get("track", default_track),
                include_paths=tuple(item.get("include_paths", [])),
            )
        )
    return sources


def fetch_company_blog(
    source: CompanyBlogConfig, max_items: int = 10, timeout: int = 8
) -> list[CompanyBlogItem]:
    response = requests.get(
        source.url,
        timeout=timeout,
        headers={"User-Agent": "AI-Daily-Update/0.1 (local knowledge base)"},
    )
    response.raise_for_status()
    return parse_company_blog_listing(response.text, source)[:max_items]


def parse_company_blog_listing(
    html: str, source: CompanyBlogConfig
) -> list[CompanyBlogItem]:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "template"]):
        element.decompose()
    source_host = urlparse(source.url).netloc.removeprefix("www.")
    items: list[CompanyBlogItem] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        title = clean_company_title(normalize_text(anchor.get_text(" ")))
        if not _looks_like_article_title(title):
            continue
        url = normalize_url(urljoin(source.url, anchor["href"]))
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"}:
            continue
        target_host = parsed_url.netloc.removeprefix("www.")
        if not _host_allowed(source_host, target_host):
            continue
        if source.include_paths and not any(
            parsed_url.path.startswith(path) for path in source.include_paths
        ):
            continue
        if url in seen_urls or title.lower() in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title.lower())
        items.append(
            CompanyBlogItem(
                source_name=source.name,
                track=source.track,
                title=title,
                url=url,
            )
        )
    return items


def fetch_all_company_blogs(
    sources: list[CompanyBlogConfig], max_per_source: int = 5, timeout: int = 8
) -> tuple[list[CompanyBlogItem], list[str]]:
    items: list[CompanyBlogItem] = []
    warnings: list[str] = []
    for source in sources:
        try:
            source_items = fetch_company_blog(source, max_items=max_per_source, timeout=timeout)
        except Exception as exc:
            warnings.append(f"{source.name}: {exc}")
            continue
        if not source_items:
            warnings.append(f"{source.name}: no article links found")
            continue
        items.extend(source_items)
    return items, warnings


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip("/") or "/",
            "",
            parsed.query,
            "",
        )
    )


def clean_company_title(title: str) -> str:
    title = re.sub(
        r"^(Product|Research|Company|Policy|News)\s+[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\s+",
        "",
        title,
    )
    title = re.sub(r"^\w{3}\s+\d{1,2},\s+\d{4}\s+·\s+", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _host_allowed(source_host: str, target_host: str) -> bool:
    return target_host == source_host or target_host.endswith(f".{source_host}")


def _looks_like_article_title(title: str) -> bool:
    if len(title) < 12 or len(title) > 180:
        return False
    lower = title.lower()
    blocked = {
        "privacy policy",
        "terms of use",
        "careers",
        "contact us",
        "sign up",
        "subscribe",
        "learn more",
        "read more",
        "view all",
        "skip to main content",
        "download press kit",
        "explore models",
        "official microsoft blog",
        "hugging face",
        "organizations",
        "technical blog",
        "daily papers",
        "team & enterprise",
        "enterprise ai",
        "large language models",
        "langsmith platform",
    }
    if lower in blocked:
        return False
    blocked_fragments = [
        "skip to ",
        "press kit",
        "privacy",
        "terms",
        "cookie",
        "subscribe",
        "newsletter",
        "你也可以阅读这篇博客",
    ]
    if "tag/" in lower or lower.startswith("tag "):
        return False
    if lower.endswith(" →") and len(lower.split()) < 8:
        return False
    if any(fragment in lower for fragment in blocked_fragments):
        return False
    return any(character.isalpha() for character in title)

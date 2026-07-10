from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from ai_daily_update.collectors.manual import ManualCandidate


TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


T = TypeVar("T")


@dataclass(frozen=True)
class DedupeResult(Generic[T]):
    unique: list[T]
    duplicates: list[T]


def dedupe_by_url(candidates: list[ManualCandidate]) -> list[ManualCandidate]:
    return dedupe_items(candidates).unique


def dedupe_items(items: list[T]) -> DedupeResult[T]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[T] = []
    duplicates: list[T] = []
    for item in items:
        url = normalize_url_for_dedupe(getattr(item, "url", ""))
        title = normalize_title_for_dedupe(getattr(item, "title", ""))
        duplicate = bool(url and url in seen_urls) or bool(title and title in seen_titles)
        if duplicate:
            duplicates.append(item)
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(item)
    return DedupeResult(unique=unique, duplicates=duplicates)


def normalize_url_for_dedupe(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path
    if netloc == "arxiv.org":
        path = path.removesuffix(".pdf")
        path = path.replace("/pdf/", "/abs/", 1)
    path = path.rstrip("/") or "/"
    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key in TRACKING_QUERY_KEYS:
            continue
        if any(lower_key.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        query_pairs.append((key, value))
    query = urlencode(query_pairs)
    return urlunparse((scheme, netloc, path, "", query, ""))


def normalize_title_for_dedupe(title: str) -> str:
    return " ".join(title.lower().split())

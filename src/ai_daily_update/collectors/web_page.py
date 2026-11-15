from __future__ import annotations

import json
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ai_daily_update.collectors.arxiv import fetch_arxiv_document, is_arxiv_url
from ai_daily_update.collectors.document import SourceDocument, normalize_text
from ai_daily_update.collectors.encoding import fix_response_encoding


def fetch_source_document(url: str, timeout: int = 20) -> SourceDocument:
    if is_arxiv_url(url):
        return fetch_arxiv_document(url, timeout=timeout)
    response = requests.get(
        url,
        timeout=timeout,
        headers={
            "User-Agent": (
                "AI-Daily-Update/0.1 "
                "(local knowledge base; contact: manual user)"
            )
        },
    )
    response.raise_for_status()
    fix_response_encoding(response)
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower() and response.text.lstrip().startswith("<") is False:
        text = normalize_text(response.text)
        return SourceDocument(url=url, title=url, description="", text=text)
    return extract_document_from_html(response.url or url, response.text)


def extract_document_from_html(url: str, html: str | bytes) -> SourceDocument:
    soup = BeautifulSoup(html, "html.parser")
    published_value = extract_publication_time(soup)
    for element in soup(["script", "style", "noscript", "svg", "template"]):
        element.decompose()
    title = extract_title(soup) or url
    description = extract_description(soup)
    article = soup.select_one("article, main, #mp-editor, .article-content")
    main = article or soup.body or soup
    text = normalize_text(main.get_text("\n"))
    event = re.search(r"^(?:事件日期|发生日期|发生时间)[：:]\s*(?:\d{4}-\d{1,2}-\d{1,2}|\d{4}年\d{1,2}月\d{1,2}日)(?:\s|$)", text, re.MULTILINE)
    return SourceDocument(url=url, title=title, description=description, text=text,
                          published=published_value, event_date_text=event[0].strip() if event else "",
                          images=extract_image_candidates(url, soup, article))


def extract_publication_time(soup: BeautifulSoup) -> str:
    published = soup.select_one('meta[property="article:published_time"], meta[itemprop="datePublished"], time[itemprop="datePublished"], time[pubdate]')
    if published:
        value = published.get("content") or published.get("datetime")
        if value:
            return value
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except ValueError:
            continue
        entries = data if isinstance(data, list) else [data]
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            entries = [*entries, *data["@graph"]]
        for entry in entries:
            if isinstance(entry, dict) and entry.get("@type") in ("NewsArticle", "Article", "BlogPosting", "TechArticle"):
                value = entry.get("datePublished")
                if isinstance(value, str):
                    return value
    return ""


def extract_image_candidates(url: str, soup: BeautifulSoup, article) -> tuple[dict[str, str], ...]:
    candidates = {}
    cover = soup.select_one('meta[property="og:image"], meta[name="twitter:image"]')
    images = [(cover.get("content"), "报道封面")] if cover else []
    if article:
        for img in article.find_all("img", limit=40):
            if img.get("width") in {"1", "2"} or img.get("height") in {"1", "2"}:
                continue
            images.append((img.get("data-src") or img.get("data-original") or img.get("src"), img.get("alt") or "报道正文图"))
    for raw, caption in images:
        if not raw or len(raw) > 2000:
            continue
        image_url = urljoin(url, raw.strip())
        if image_url.startswith(("https://", "http://")):
            candidates.setdefault(image_url, {"url": image_url, "caption": caption.strip()[:160]})
        if len(candidates) == 8:
            break
    return tuple(candidates.values())


def extract_title(soup: BeautifulSoup) -> str:
    for selector in [
        ('meta', {"property": "og:title"}),
        ('meta', {"name": "twitter:title"}),
    ]:
        element = soup.find(*selector)
        if element and element.get("content"):
            return normalize_text(element["content"])
    if soup.title and soup.title.string:
        return normalize_text(soup.title.string)
    h1 = soup.find("h1")
    if h1:
        return normalize_text(h1.get_text(" "))
    return ""


def extract_description(soup: BeautifulSoup) -> str:
    for selector in [
        ('meta', {"name": "description"}),
        ('meta', {"property": "og:description"}),
        ('meta', {"name": "twitter:description"}),
    ]:
        element = soup.find(*selector)
        if element and element.get("content"):
            return normalize_text(element["content"])
    return ""


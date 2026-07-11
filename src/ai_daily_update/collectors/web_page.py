from __future__ import annotations

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
    return extract_document_from_html(url, response.text)


def extract_document_from_html(url: str, html: str) -> SourceDocument:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "template"]):
        element.decompose()
    title = extract_title(soup) or url
    description = extract_description(soup)
    main = soup.find("main") or soup.find("article") or soup.body or soup
    text = normalize_text(main.get_text("\n"))
    return SourceDocument(url=url, title=title, description=description, text=text)


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


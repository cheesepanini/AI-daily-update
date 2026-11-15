from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from ai_daily_update.collectors.arxiv import extract_arxiv_id, fetch_arxiv_document, is_arxiv_url
from ai_daily_update.collectors.document import SourceDocument, normalize_text
from ai_daily_update.collectors.encoding import fix_response_encoding
from ai_daily_update.utils.dates import written_dates


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
    published_value = extract_publication_time(soup, url)
    for element in soup(["script", "style", "noscript", "svg", "template"]):
        element.decompose()
    title = extract_title(soup) or url
    description = extract_description(soup)
    article = soup.select_one("#mp-editor, #vs, .article-content, .entry-content, .c-article-body, .ltx_document")
    article = article or soup.select_one("article, .article") or soup.select_one("main")
    main = article or soup.body or soup
    text = normalize_text(main.get_text("\n"))
    event = re.search(r"^(?:事件日期|事件时间|发生日期|发生时间)[：:]\s*(?:\d{4}-\d{1,2}-\d{1,2}|\d{4}年\d{1,2}月\d{1,2}日)(?:\s|$)", text, re.MULTILINE)
    event_text = event[0].strip() if event else ""
    arxiv_id = extract_arxiv_id(url)
    if arxiv_id and "/html/" not in urlsplit(url).path:
        if published_value and (arxiv_id.endswith("v1") or "v" not in arxiv_id):
            event_text = f"arXiv 首版发布 {published_value}"
        license_link = soup.select_one('#license a, .license a, a[rel="license"]')
        license_url = license_link.get("href", "") if license_link else ""
        # arXiv's abstract-page license applies to the exact paper version.
        if not license_url:
            license_url = next((a["href"] for a in soup.select("a[href]") if a.get_text(strip=True) == "view license"), "")
        return SourceDocument(url=url, title=title, description=description, text=text,
                              published=published_value, event_date_text=event_text, image_license=license_url)
    if published_value and not event_text and urlsplit(url).hostname == "www.nature.com":
        article_type = soup.select_one(".c-article-identifiers__type")
        if article_type and article_type.get_text(strip=True).casefold() in {"article", "research article"}:
            event_text = f"期刊原文上线发表 {published_value}"
    return SourceDocument(url=url, title=title, description=description, text=text,
                          published=published_value, event_date_text=event_text,
                          images=extract_image_candidates(url, soup, article))


def extract_publication_time(soup: BeautifulSoup, url: str) -> str:
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
            kind = entry.get("@type", []) if isinstance(entry, dict) else []
            kinds = [kind] if isinstance(kind, str) else kind
            if isinstance(kinds, list) and any(v in ("NewsArticle", "Article", "BlogPosting", "TechArticle", "ScholarlyArticle", "ReportageNewsArticle") for v in kinds):
                value = entry.get("datePublished")
                if isinstance(value, str):
                    return value
    for name in ("citation_online_date", "citation_publication_date", "prism.publicationDate", "citation_date"):
        meta = soup.find("meta", attrs={"name": name})
        if meta and meta.get("content"):
            return re.sub(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", r"\1-\2-\3", meta["content"].strip())
    for element in soup.select('time, [class*="publish-time"], [class*="publish-date"]'):
        label = f'{element.get("aria-label", "")} {element.get_text(" ", strip=True)}'
        if re.match(r"^\s*(Published\b|发布时间|发布日期|发布于|发表时间)", label, re.I):
            dates = written_dates(element.get("datetime") or label)
            if len(dates) == 1:
                return next(iter(dates))
    source_date = {"www.qbitai.com": ".article_info .date", "m.sohu.com": ".author-info"}
    selector = source_date.get(urlsplit(url).hostname)
    if selector and (element := soup.select_one(selector)):
        dates = written_dates(element.get_text(" ", strip=True))
        if len(dates) == 1:
            return next(iter(dates))
    heading = soup.find("h1")
    if heading:
        vicinity = heading.find_parent("header") or heading.parent
        for element in vicinity.select("time, [class*=publish-date]"):
            if not re.search(r"updat|modif|更新", (str(element.attrs) + element.get_text(" ", strip=True)), re.I):
                dates = written_dates(element.get("datetime") or element.get_text(" ", strip=True))
                if len(dates) == 1:
                    return next(iter(dates))
    return ""


def extract_image_candidates(url: str, soup: BeautifulSoup, article) -> tuple[dict[str, str], ...]:
    candidates = {}
    cover = soup.select_one('meta[property="og:image"], meta[name="twitter:image"]')
    images = [(cover.get("content"), "报道封面")] if cover else []
    if article:
        for img in article.find_all("img", limit=120):
            if img.find_parent(["aside", "header", "nav", "footer"]) or img.find_parent(class_="c-article-recommendations-list"):
                continue
            if img.get("width") in {"1", "2"} or img.get("height") in {"1", "2"}:
                continue
            srcset = img.get("data-srcset") or img.get("srcset") or ""
            raw = img.get("data-src") or img.get("data-original") or img.get("data-lazy-src")
            if not raw and srcset:
                options = [option.strip().split() for option in srcset.split(",") if option.strip()]
                raw = options[-1][0] if options else ""
            figure = img.find_parent("figure")
            figcaption = figure.find("figcaption") if figure else None
            caption = figcaption.get_text(" ", strip=True) if figcaption else img.get("alt")
            images.append((raw or img.get("src"), caption or "报道正文图"))
    for raw, caption in images:
        if not raw or len(raw) > 2000:
            continue
        image_url = urljoin(url, raw.strip())
        if image_url.startswith(("https://", "http://")) and not re.search(r"[/_-](?:logo|placeholder|avatar|icon|qrcode|pixel|tracking)[-_./]", image_url, re.I):
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


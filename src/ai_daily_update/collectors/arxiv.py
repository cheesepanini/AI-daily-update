from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date
from urllib.parse import quote, urlparse

import requests

from ai_daily_update.collectors.document import SourceDocument, normalize_text


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def extract_arxiv_id(url_or_id: str) -> str | None:
    value = url_or_id.strip()
    if re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", value):
        return value
    parsed = urlparse(value)
    if parsed.netloc not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
        return None
    match = re.search(r"/(?:abs|pdf|html)/([^/?#]+)", parsed.path)
    if not match:
        return None
    arxiv_id = match.group(1)
    arxiv_id = arxiv_id.removesuffix(".pdf")
    return arxiv_id if re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", arxiv_id) else None


def is_arxiv_url(url: str) -> bool:
    return extract_arxiv_id(url) is not None


def fetch_arxiv_document(url_or_id: str, timeout: int = 20) -> SourceDocument:
    arxiv_id = extract_arxiv_id(url_or_id)
    if not arxiv_id:
        raise ValueError(f"Not an arXiv abs/pdf/html URL or id: {url_or_id}")
    response = requests.get(
        f"{ARXIV_API_URL}?id_list={quote(arxiv_id)}",
        timeout=timeout,
        headers={"User-Agent": "AI-Daily-Update/0.1 (local knowledge base)"},
    )
    response.raise_for_status()
    return parse_arxiv_atom(response.text, requested_id=arxiv_id)


def search_latest_arxiv(
    categories: list[str],
    max_results: int = 10,
    from_date: date | None = None,
    to_date: date | None = None,
    timeout: int = 20,
) -> list[SourceDocument]:
    query = build_arxiv_search_query(categories, from_date=from_date, to_date=to_date)
    response = requests.get(
        ARXIV_API_URL,
        params={
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        },
        timeout=timeout,
        headers={"User-Agent": "AI-Daily-Update/0.1 (local knowledge base)"},
    )
    response.raise_for_status()
    return parse_arxiv_feed(response.text)


def build_arxiv_search_query(
    categories: list[str], from_date: date | None = None, to_date: date | None = None
) -> str:
    category_query = " OR ".join(f"cat:{category}" for category in categories)
    if len(categories) > 1:
        category_query = f"({category_query})"
    if from_date or to_date:
        start = _arxiv_date_start(from_date) if from_date else "000101010000"
        end = _arxiv_date_end(to_date) if to_date else "999912312359"
        return f"{category_query} AND submittedDate:[{start} TO {end}]"
    return category_query


def parse_arxiv_feed(xml_text: str) -> list[SourceDocument]:
    root = ET.fromstring(xml_text)
    documents: list[SourceDocument] = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        documents.append(_document_from_entry(entry))
    return documents


def parse_arxiv_atom(xml_text: str, requested_id: str) -> SourceDocument:
    root = ET.fromstring(xml_text)
    entry = root.find(f"{ATOM_NS}entry")
    if entry is None:
        raise ValueError(f"arXiv API returned no entry for {requested_id}")
    return _document_from_entry(entry, requested_id=requested_id)


def _document_from_entry(entry: ET.Element, requested_id: str | None = None) -> SourceDocument:
    title = normalize_text(_text(entry, f"{ATOM_NS}title"))
    summary = normalize_text(_text(entry, f"{ATOM_NS}summary"))
    published = _text(entry, f"{ATOM_NS}published")
    updated = _text(entry, f"{ATOM_NS}updated")
    authors = [
        normalize_text(_text(author, f"{ATOM_NS}name"))
        for author in entry.findall(f"{ATOM_NS}author")
    ]
    authors = [author for author in authors if author]
    primary_category_element = entry.find(f"{ARXIV_NS}primary_category")
    primary_category = (
        primary_category_element.attrib.get("term", "")
        if primary_category_element is not None
        else ""
    )
    categories = [
        category.attrib.get("term", "")
        for category in entry.findall(f"{ATOM_NS}category")
        if category.attrib.get("term")
    ]
    doi = _text(entry, f"{ARXIV_NS}doi")
    journal_ref = _text(entry, f"{ARXIV_NS}journal_ref")
    entry_id = _text(entry, f"{ATOM_NS}id")
    arxiv_id = requested_id or _id_from_entry_url(entry_id) or "unknown"
    canonical_url = f"https://arxiv.org/abs/{arxiv_id}"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    text_lines = [
        f"Title: {title}",
        f"arXiv ID: {arxiv_id}",
        f"Authors: {', '.join(authors)}",
        f"Published: {published}",
        f"Updated: {updated}",
        f"Primary category: {primary_category}",
        f"Categories: {', '.join(categories)}",
    ]
    if doi:
        text_lines.append(f"DOI: {doi}")
    if journal_ref:
        text_lines.append(f"Journal reference: {journal_ref}")
    text_lines.extend(
        [
            "",
            "Abstract:",
            summary,
            "",
            f"Abstract URL: {canonical_url}",
            f"PDF URL: {pdf_url}",
        ]
    )
    return SourceDocument(
        url=canonical_url,
        title=title,
        description=summary,
        text="\n".join(text_lines),
    )


def _text(element: ET.Element, path: str) -> str:
    found = element.find(path)
    return found.text or "" if found is not None else ""


def _id_from_entry_url(entry_id: str) -> str | None:
    if not entry_id:
        return None
    return extract_arxiv_id(entry_id)


def _arxiv_date_start(value: date) -> str:
    return value.strftime("%Y%m%d") + "0000"


def _arxiv_date_end(value: date) -> str:
    return value.strftime("%Y%m%d") + "2359"

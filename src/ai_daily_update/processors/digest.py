from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from ai_daily_update.collectors.document import SourceDocument
from ai_daily_update.processors.candidates import Candidate


CHINESE_NUMERAL_HEADING_RE = re.compile(
    r"^(?P<number>[一二三四五六七八九十百]+)[、.．]\s*(?P<title>.+)$"
)
NUMBERED_DETAIL_RE = re.compile(r"^\d+[、.．]\s*(?P<text>.+)$")
DATE_IN_TITLE_RE = re.compile(r"(20\d{2})[.\-/年]?\s*(\d{1,2})[.\-/月]?\s*(\d{1,2})")


@dataclass(frozen=True)
class DigestItem:
    title: str
    summary: str
    index: int


def should_split_digest(candidate: Candidate) -> bool:
    if candidate.source_name != "腾讯研究院":
        return False
    title = candidate.title
    return "AI速递" in title or "AI 速递" in title or "速递" in title


def split_digest_document(document: SourceDocument) -> list[DigestItem]:
    items: list[DigestItem] = []
    current_title = ""
    current_lines: list[str] = []

    for raw_line in document.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = CHINESE_NUMERAL_HEADING_RE.match(line)
        if heading_match:
            _append_digest_item(items, current_title, current_lines)
            current_title = heading_match.group("title").strip()
            current_lines = []
            continue
        if not current_title:
            continue
        detail_match = NUMBERED_DETAIL_RE.match(line)
        if detail_match:
            current_lines.append(detail_match.group("text").strip())
        elif _looks_like_continuation(line):
            current_lines.append(line)

    _append_digest_item(items, current_title, current_lines)
    return items


def expand_digest_candidate(candidate: Candidate, document: SourceDocument) -> list[Candidate]:
    items = split_digest_document(document)
    if not items:
        return [candidate]
    published = candidate.published or published_date_from_digest_title(document.title or candidate.title)
    return [
        Candidate(
            url=digest_item_url(candidate.url, item.index),
            track=candidate.track,
            topics=candidate.topics,
            title=item.title,
            summary=item.summary,
            source_kind=candidate.source_kind,
            source_name=candidate.source_name,
            published=published,
            parent_url=candidate.url,
            parent_title=document.title or candidate.title,
            digest_item_index=item.index,
        )
        for item in items
    ]


def published_date_from_digest_title(title: str) -> str:
    match = DATE_IN_TITLE_RE.search(title)
    if not match:
        return ""
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""


def digest_item_url(parent_url: str, index: int) -> str:
    parsed = urlparse(parent_url)
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() != "digest_item"
    ]
    query_pairs.append(("digest_item", str(index)))
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_pairs),
            parsed.fragment,
        )
    )


def _append_digest_item(items: list[DigestItem], title: str, lines: list[str]) -> None:
    summary = " ".join(line.rstrip("；;。") for line in lines if line).strip()
    if not title or len(summary) < 20:
        return
    items.append(DigestItem(title=title, summary=summary, index=len(items) + 1))


def _looks_like_continuation(line: str) -> bool:
    blocked = {"生成式AI", "前沿科技", "报告观点"}
    if line in blocked:
        return False
    if len(line) < 12:
        return False
    return bool(re.search(r"[，。；;]", line))

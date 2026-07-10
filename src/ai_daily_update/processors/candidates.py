from __future__ import annotations

from dataclasses import dataclass, replace

from ai_daily_update.collectors.arxiv import extract_arxiv_id
from ai_daily_update.collectors.company_blogs import CompanyBlogItem
from ai_daily_update.collectors.document import SourceDocument
from ai_daily_update.collectors.manual import ManualCandidate
from ai_daily_update.collectors.rss import RSSItem


@dataclass(frozen=True)
class Candidate:
    url: str
    track: str
    topics: list[str]
    title: str
    summary: str = ""
    source_kind: str = "manual"
    source_name: str = ""
    published: str = ""
    score: float = 0.0
    score_reasons: tuple[str, ...] = ()
    parent_url: str = ""
    parent_title: str = ""
    digest_item_index: int = 0


def candidate_from_manual(candidate: ManualCandidate) -> Candidate:
    return Candidate(
        url=candidate.url,
        track=candidate.track,
        topics=candidate.topics,
        title=candidate.title,
        source_kind="manual",
        source_name="manual_urls",
    )


def candidate_from_arxiv_document(document: SourceDocument) -> Candidate:
    arxiv_id = extract_arxiv_id(document.url) or document.url
    return Candidate(
        url=document.url,
        track="academic",
        topics=["foundation-model"],
        title=document.title or arxiv_id,
        summary=document.description,
        source_kind="arxiv",
        source_name="arXiv",
        published=_line_value(document.text, "Published:"),
    )


def candidate_from_rss_item(item: RSSItem) -> Candidate:
    return Candidate(
        url=item.url,
        track=item.track,
        topics=[],
        title=item.title,
        summary=item.summary,
        source_kind="chinese_media" if item.feed_name in CHINESE_MEDIA_SOURCES else "rss",
        source_name=item.feed_name,
        published=item.published,
    )


def candidate_from_company_item(item: CompanyBlogItem) -> Candidate:
    return Candidate(
        url=item.url,
        track=item.track,
        topics=[],
        title=item.title,
        source_kind=source_kind_for_company_item(item.source_name),
        source_name=item.source_name,
    )


def with_updates(candidate: Candidate, **updates) -> Candidate:
    return replace(candidate, **updates)


def _line_value(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return ""


def source_kind_for_company_item(source_name: str) -> str:
    if source_name in BENCHMARK_SOURCES:
        return "benchmark"
    if source_name in CHINESE_MEDIA_SOURCES:
        return "chinese_media"
    return "company_blog"


CHINESE_MEDIA_SOURCES = {
    "机器之心",
    "量子位",
    "新智元",
    "腾讯研究院",
}


BENCHMARK_SOURCES = {
    "Arena.ai",
    "Artificial Analysis",
    "OpenRouter",
    "Stanford HELM",
}

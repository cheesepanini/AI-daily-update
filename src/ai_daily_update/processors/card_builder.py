from __future__ import annotations

from datetime import date, datetime
from email.utils import parsedate_to_datetime
import re
from urllib.parse import urlparse

from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.utils.dates import now_iso
from ai_daily_update.utils.slug import slugify


ACADEMIC_SECTIONS = [
    "一句话结论",
    "研究问题",
    "方法要点",
    "主要结果",
    "为什么重要",
    "与既有脉络的关系",
    "局限与不确定性",
    "可用于图书更新的角度",
    "可用于 PPT 的表达",
    "原始材料",
]

INDUSTRY_SECTIONS = [
    "一句话结论",
    "事件概述",
    "涉及主体",
    "产业意义",
    "与技术脉络的关系",
    "可验证信息",
    "潜在夸大或不确定性",
    "可用于简报/公众号的角度",
    "可用于 PPT 的表达",
    "原始材料",
]


def build_card_metadata(candidate: Candidate, day: date, timezone: str) -> dict:
    source_date = candidate_date(candidate, fallback=day)
    source_type = source_type_for_candidate(candidate)
    domain = urlparse(candidate.url).netloc
    metadata = {
        "id": build_card_id(candidate, source_date),
        "track": candidate.track,
        "title_zh": "待补充中文标题",
        "title_en": candidate.title,
        "date": source_date.isoformat(),
        "collected_date": day.isoformat(),
        "source_type": source_type,
        "source_url": candidate.url,
        "primary_source": True,
        "topics": candidate.topics,
        "keywords_en": candidate.topics,
        "entities": [domain] if domain else [],
        # Unscored until a human (or a future LLM scoring step) actually
        # assesses the card. Defaulting these to a fabricated "medium" rating
        # (e.g. 3) would let unreviewed cards silently drive both the
        # auto-review accept/reject decision and the public-brief filter
        # (`public_brief_potential >= 3`) as if someone had vetted them.
        "importance": 0,
        "novelty": 0,
        "confidence": 0,
        "book_potential": 0,
        "ppt_potential": 0,
        "public_brief_potential": 0,
        "review_status": "needs-review",
        "created_at": now_iso(timezone),
    }
    if candidate.track == "industry":
        metadata["industry_dimensions"] = ["company"]
    if candidate.parent_url:
        metadata["parent_source_url"] = candidate.parent_url
    if candidate.parent_title:
        metadata["parent_source_title"] = candidate.parent_title
    if candidate.digest_item_index:
        metadata["digest_item_index"] = candidate.digest_item_index
    return metadata


def source_type_for_candidate(candidate: Candidate) -> str:
    if candidate.source_kind == "benchmark":
        return "benchmark-update"
    if candidate.digest_item_index:
        return "chinese-media-digest-item"
    if candidate.source_kind == "chinese_media":
        return "chinese-media"
    if candidate.track == "academic":
        return "paper"
    return "company-news"


def build_card_id(candidate: Candidate, card_date: date) -> str:
    topic_part = "-".join(candidate.topics[:2])
    title_slug = slugify(candidate.title or candidate.url, fallback="manual-source")
    return f"{card_date.isoformat()}-{candidate.track}-{topic_part}-{title_slug[:48]}".strip("-")


def apply_content_date(metadata: dict, candidate: Candidate, content: str) -> dict:
    content_date = infer_date_from_content(content)
    if not content_date:
        return metadata
    metadata = dict(metadata)
    metadata["event_date"] = content_date.isoformat()
    if not candidate.published:
        metadata["date"] = content_date.isoformat()
        metadata["id"] = build_card_id(candidate, content_date)
    return metadata


def candidate_date(candidate: Candidate, fallback: date) -> date:
    if candidate.published:
        parsed = parse_source_date(candidate.published)
        if parsed:
            return parsed
    return fallback


def infer_date_from_content(content: str) -> date | None:
    for line in content.splitlines():
        if "发布日期" in line or "发布" in line or "事件" in line:
            parsed = parse_date_from_text(line)
            if parsed:
                return parsed
    for line in content.splitlines():
        parsed = parse_date_from_text(line)
        if parsed:
            return parsed
    return None


def parse_date_from_text(text: str) -> date | None:
    iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
    if iso_match:
        return _date_from_parts(*iso_match.groups())
    zh_match = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if zh_match:
        return _date_from_parts(*zh_match.groups())
    return None


def _date_from_parts(year: str, month: str, day: str) -> date | None:
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def parse_source_date(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text).date()
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def build_placeholder_content(candidate: Candidate) -> str:
    sections = ACADEMIC_SECTIONS if candidate.track == "academic" else INDUSTRY_SECTIONS
    body = []
    for section in sections:
        body.append(f"## {section}")
        if section == "一句话结论":
            body.append("待 review：该卡片由手动 URL 生成，请根据原始材料补全事实与判断。")
        elif section == "原始材料":
            body.append(f"- {candidate.url}")
        else:
            body.append("待补充。")
        body.append("")
    return "\n".join(body).rstrip() + "\n"


def card_path(markdown_root, day: date, card_id: str):
    return markdown_root / "cards" / f"{day.year:04d}" / f"{day.month:02d}" / f"{card_id}.md"

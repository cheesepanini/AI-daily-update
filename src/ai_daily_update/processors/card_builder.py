from __future__ import annotations

from datetime import date, datetime
from email.utils import parsedate_to_datetime
import json
import re
from typing import Any
from urllib.parse import urlparse

from ai_daily_update.processors.candidates import Candidate
from ai_daily_update.utils.dates import now_iso
from ai_daily_update.utils.slug import slugify


QUALITY_SCORE_FIELDS = [
    "importance",
    "novelty",
    "confidence",
    "book_potential",
    "ppt_potential",
    "public_brief_potential",
]


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


def score_card_quality_with_llm(
    metadata: dict, content: str, llm_client: Any | None
) -> dict[str, int]:
    """Ask the LLM to rate a freshly generated card 1-5 on each quality field.

    Only called on genuinely LLM-generated content (never on placeholder
    text), so a low score is a real signal rather than noise. Returns {} on
    any failure so callers keep the metadata's existing (0 = unscored) values
    instead of a fabricated one.
    """
    if not llm_client or not getattr(llm_client, "available", False):
        return {}
    prompt = build_card_quality_prompt(metadata, content)
    try:
        response = llm_client.generate_card_content(prompt)
    except Exception:
        return {}
    return parse_card_quality_response(response) or {}


def build_card_quality_prompt(metadata: dict, content: str) -> str:
    return (
        "你是中文 AI 知识库质量评审员。请为下面这张刚生成的知识卡片打分（1-5 分，5 分最高）。\n"
        "字段含义：\n"
        "- importance：对 AI 行业/学术前沿的重要程度。\n"
        "- novelty：信息的新颖度，是否是新进展而非旧消息重复。\n"
        "- confidence：正文事实的可信度（是否有明确来源、是否有“待核实”标注）。\n"
        "- book_potential：是否适合用于图书内容更新。\n"
        "- ppt_potential：是否适合用于 PPT 讲稿。\n"
        "- public_brief_potential：是否适合放进面向公众的简报。\n"
        "要求：\n"
        "1. 只输出 JSON，不要 Markdown，不要解释。\n"
        "2. 输出格式为 "
        '{"scores":{"importance":1-5,"novelty":1-5,"confidence":1-5,'
        '"book_potential":1-5,"ppt_potential":1-5,"public_brief_potential":1-5}}。\n'
        "3. 六个字段都必须给分，不要遗漏，也不要用 0。\n\n"
        f"title: {metadata.get('title_zh') or metadata.get('title_en', '')}\n"
        f"track: {metadata.get('track', '')}\n"
        f"topics: {', '.join(metadata.get('topics', []) or [])}\n\n"
        f"正文：\n{content[:4000]}"
    )


def parse_card_quality_response(content: str | None) -> dict[str, int] | None:
    if not content:
        return None
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("scores"), dict):
        return None
    scores: dict[str, int] = {}
    for field in QUALITY_SCORE_FIELDS:
        try:
            value = int(parsed["scores"][field])
        except (KeyError, TypeError, ValueError):
            continue
        scores[field] = max(1, min(5, value))
    if len(scores) < len(QUALITY_SCORE_FIELDS):
        return None
    return scores

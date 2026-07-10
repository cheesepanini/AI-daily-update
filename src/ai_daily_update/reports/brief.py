from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from ai_daily_update.storage import db


TITLES = {
    "academic": "AI 学术前沿简报",
    "industry": "AI 产业观察简报",
    "book": "图书内容更新候选",
    "public": "本月 AI 进展观察",
}


def generate_brief(
    sqlite_path: Path,
    output_root: Path,
    from_date: str,
    to_date: str,
    topics: list[str] | None,
    audience: str,
    date_basis: str = "collected",
) -> Path:
    connection = db.connect(sqlite_path)
    rows = db.query_cards(connection, from_date, to_date, topics, audience, date_basis=date_basis)
    connection.close()
    items = [brief_item_from_row(row) for row in rows]
    title = TITLES.get(audience, "AI 简报")
    basis_label = "收集/入库日期" if date_basis == "collected" else "事件/发布日期"
    lines = [
        f"# {title}: {from_date} 至 {to_date}",
        "",
        f"> 日期口径：{basis_label}",
        "",
        "## 核心判断",
        "",
        build_core_judgement(items, audience),
        "",
        "## 重要进展",
        "",
    ]
    if not items:
        lines.append("暂无符合条件的 accepted 卡片。")
    for item in items:
        date_lines = [f"- 事件日期：{item['event_date']}"]
        if item["info_date"] and item["info_date"] != item["event_date"]:
            date_lines.append(f"- 信息日期：{item['info_date']}")
        if item["collected_date"] != item["info_date"]:
            date_lines.append(f"- 入库日期：{item['collected_date']}")
        lines.extend(
            [
                f"### {item['title']}",
                "",
                *date_lines,
                f"- 来源：[{item['source_label']}]({item['source_url']})",
                f"- 主题：{item['topics']}",
                f"- 一句话：{item['conclusion']}",
                f"- 事件概述：{item['overview']}",
                f"- 简报价值：{item['value']}",
                "",
            ]
        )
    lines.extend(["## 后续关注", ""])
    if items:
        for item in items:
            lines.append(f"- {item['title']}：{item['follow_up']}")
    else:
        lines.append("暂无。")
    lines.extend(["## 参考材料", ""])
    for item in items:
        lines.append(f"- [{item['title_en'] or item['title']}]({item['source_url']})")
    output_dir = output_root / "briefs" / audience
    output_dir.mkdir(parents=True, exist_ok=True)
    topic_part = "-".join(topics or ["all"])
    output_path = unique_brief_path(output_dir, from_date, to_date, topic_part, date_basis)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def unique_brief_path(
    output_dir: Path, from_date: str, to_date: str, topic_part: str, date_basis: str
) -> Path:
    base_name = f"{from_date}_to_{to_date}_{date_basis}_{topic_part}"
    output_path = output_dir / f"{base_name}.md"
    if not output_path.exists():
        return output_path
    index = 2
    while True:
        candidate = output_dir / f"{base_name}-{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def brief_item_from_row(row) -> dict[str, str]:
    path = Path(row["path"])
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    sections = extract_sections(content)
    title = row["title_zh"] or row["title_en"] or row["id"]
    topics = ", ".join(json.loads(row["topics"] or "[]")) or "未标注"
    return {
        "title": title,
        "title_en": row["title_en"] or "",
        "date": row["event_date"] or row["date"],
        "event_date": row["event_date"] or row["date"],
        "info_date": row["date"],
        "collected_date": row["collected_date"] or row["date"],
        "track": row["track"],
        "topics": topics,
        "source_url": row["source_url"] or "",
        "source_label": source_label(row["source_url"] or ""),
        "conclusion": first_available(
            sections,
            ["一句话结论"],
            fallback=f"{title} 已入选本期简报。",
        ),
        "overview": first_available(
            sections,
            ["事件概述", "研究问题", "事件概述 / 研究问题", "事件概述或研究问题"],
            fallback="卡片未提供事件概述。",
        ),
        "value": first_available(
            sections,
            ["为什么重要", "产业意义", "主要结果", "主要结果 / 产业意义", "主要结果或产业意义"],
            fallback="可作为本期 AI 进展观察素材。",
        ),
        "follow_up": first_available(
            sections,
            ["局限与不确定性", "潜在夸大或不确定性", "可验证信息"],
            fallback="后续关注来源更新、复现材料和实际应用反馈。",
        ),
    }


def build_core_judgement(items: list[dict[str, str]], audience: str) -> str:
    if not items:
        return "本期没有符合条件的已接受卡片，暂不形成简报判断。"
    tracks = {item["track"] for item in items}
    if audience == "academic" or tracks == {"academic"}:
        focus = "主要集中在学术前沿与方法进展"
    elif audience == "industry" or tracks == {"industry"}:
        focus = "主要集中在产业发布、产品能力和落地信号"
    else:
        focus = "覆盖学术研究与产业动态"
    topic_counts: dict[str, int] = {}
    for item in items:
        for topic in [part.strip() for part in item["topics"].split(",") if part.strip()]:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    top_topics = ", ".join(
        topic for topic, _ in sorted(topic_counts.items(), key=lambda pair: pair[1], reverse=True)[:3]
    )
    topic_sentence = f"，高频主题包括 {top_topics}" if top_topics else ""
    return f"本期共纳入 {len(items)} 条已审核通过的 AI 信息，{focus}{topic_sentence}。"


def extract_sections(content: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in content.splitlines():
        stripped = line.strip()
        heading = section_heading(stripped)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        if current and stripped:
            sections[current].append(stripped.lstrip("- ").strip())
    return {
        heading: compact_text(" ".join(lines))
        for heading, lines in sections.items()
        if compact_text(" ".join(lines))
    }


def section_heading(line: str) -> str:
    if line.startswith("## "):
        return line.lstrip("#").strip()
    if line.startswith("**") and line.rstrip().endswith("**"):
        return line.strip("*").strip()
    return ""


def first_available(sections: dict[str, str], prefixes: list[str], fallback: str) -> str:
    for prefix in prefixes:
        for heading, text in sections.items():
            if heading.startswith(prefix) and text:
                return text
    return fallback


def compact_text(text: str, max_chars: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def source_label(source_url: str) -> str:
    host = urlparse(source_url).netloc.lower().removeprefix("www.")
    if host == "arxiv.org":
        return "arXiv 论文"
    if host.endswith("openai.com"):
        return "OpenAI"
    if host.endswith("anthropic.com"):
        return "Anthropic"
    if host.endswith("deepseek.com"):
        return "DeepSeek"
    return host or "原始来源"

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from ai_daily_update.storage.markdown import iter_cards, read_card


def needs_review_cards(markdown_root: Path, limit: int = 12) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in iter_cards(markdown_root):
        card = read_card(path)
        if card.metadata.get("review_status") != "needs-review":
            continue
        cards.append(
            {
                "path": path,
                "metadata": card.metadata,
                "content": card.content,
            }
        )
    cards.sort(
        key=lambda item: (
            str(item["metadata"].get("date", "")),
            str(item["metadata"].get("created_at", "")),
        ),
        reverse=True,
    )
    return cards[:limit]


def build_review_summary_prompt(cards: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for index, card in enumerate(cards, start=1):
        metadata = card["metadata"]
        content = card["content"][:1800]
        blocks.append(
            f"""
[{index}]
title_zh: {metadata.get('title_zh', '')}
title_en: {metadata.get('title_en', '')}
track: {metadata.get('track', '')}
topics: {', '.join(metadata.get('topics', []))}
source_url: {metadata.get('source_url', '')}
importance: {metadata.get('importance', '')}
novelty: {metadata.get('novelty', '')}
confidence: {metadata.get('confidence', '')}
content_excerpt:
{content}
"""
        )
    return f"""
你是 AI-Daily-Update 的中文审核助手。请帮助用户快速 review needs-review 卡片。

要求：
- 输出 Markdown。
- 尽量短，但信息要足够充分。
- 不要复述长段正文。
- 每张卡片给出一个建议动作：建议接受 / 建议稍后 / 建议拒绝。
- 说明理由时必须关注：来源可靠性、信息密度、是否值得入库、是否有明显不确定性。
- 如果内容只是占位、明显缺事实、或来源无法验证，倾向建议稍后或拒绝。

输出结构：

# 待审核内容速览

## 总体判断

## 优先处理

| 序号 | 标题 | 建议 | 一句话理由 | 风险/不确定性 |
| --- | --- | --- | --- | --- |

## 逐条备注

以下是待审核卡片：

{''.join(blocks)}
"""


def write_review_summary(markdown_root: Path, day: date, content: str) -> Path:
    output_dir = markdown_root / "inbox"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{day.isoformat()}-review-summary.md"
    output_path.write_text(content.strip() + "\n", encoding="utf-8")
    return output_path


def deterministic_review_summary(cards: list[dict[str, Any]]) -> str:
    lines = [
        "# 待审核内容速览",
        "",
        "## 总体判断",
        "",
        "未配置可用 LLM，以下为基于元数据的占位审核摘要。",
        "",
        "## 优先处理",
        "",
        "| 序号 | 标题 | 建议 | 一句话理由 | 风险/不确定性 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for index, card in enumerate(cards, start=1):
        metadata = card["metadata"]
        title = metadata.get("title_zh") or metadata.get("title_en") or metadata.get("id")
        confidence = metadata.get("confidence", "")
        suggestion = "建议稍后" if confidence and int(confidence) < 3 else "建议接受"
        lines.append(
            f"| {index} | {title} | {suggestion} | 待人工确认事实与表达质量 | 需要打开来源核对 |"
        )
    return "\n".join(lines)

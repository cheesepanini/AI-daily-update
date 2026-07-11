from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from ai_daily_update.ppt.corpus import (
    PPTNodeMatch,
    RegisteredPPTNode,
    group_ppt_topic_nodes,
    match_registered_nodes,
    matching_terms,
    read_ppt_entries,
    read_ppt_node_registry,
)
from ai_daily_update.reports.brief import extract_sections, first_available
from ai_daily_update.storage.markdown import iter_cards, read_card
from ai_daily_update.trends import trend_group_count, trend_term_groups


@dataclass(frozen=True)
class PPTCardSuggestion:
    card_id: str
    title: str
    source_url: str
    date: str
    topics: list[str]
    conclusion: str
    overview: str
    node_id: str
    node_label: str
    score: int
    reasons: list[str]


@dataclass(frozen=True)
class PPTSectionTrendSuggestion:
    level1: str
    level2: str
    pages: list[int]
    card_ids: list[str]
    card_count: int
    trends: list[dict[str, Any]]
    recommendation: str

    @property
    def label(self) -> str:
        return " / ".join(part for part in [self.level1, self.level2] if part) or "未匹配小节"


def generate_ppt_plan(
    markdown_root: Path,
    ppt_csv_path: Path,
    node_registry_path: Path,
    from_date: str,
    to_date: str,
    date_basis: str = "collected",
    status: str = "accepted",
    topics_config: dict[str, Any] | None = None,
    deck_id: str = "",
    deck_title: str = "",
    deck_version: str = "",
    llm_client: Any | None = None,
) -> Path:
    node_matches = load_ppt_node_matches(ppt_csv_path, node_registry_path)
    cards = load_cards_for_ppt_plan(markdown_root, from_date, to_date, date_basis, status)
    suggestions = match_cards_to_nodes(cards, [match.registered for match in node_matches])
    section_trends = summarize_level2_trends(node_matches, suggestions, topics_config or {})
    output_path = write_ppt_plan(
        markdown_root,
        from_date,
        to_date,
        date_basis,
        status,
        node_matches,
        suggestions,
        section_trends,
        deck_id=deck_id,
        deck_title=deck_title,
        deck_version=deck_version,
        llm_client=llm_client,
    )
    return output_path


def load_ppt_node_matches(ppt_csv_path: Path, node_registry_path: Path) -> list[PPTNodeMatch]:
    entries = read_ppt_entries(ppt_csv_path)
    current_nodes = group_ppt_topic_nodes(entries)
    registered_nodes = [
        node for node in read_ppt_node_registry(node_registry_path) if node.status == "active"
    ]
    return match_registered_nodes(registered_nodes, current_nodes)


def load_cards_for_ppt_plan(
    markdown_root: Path, from_date: str, to_date: str, date_basis: str, status: str
) -> list[dict[str, Any]]:
    items = []
    start = date.fromisoformat(from_date)
    end = date.fromisoformat(to_date)
    for path in iter_cards(markdown_root):
        card = read_card(path)
        metadata = card.metadata
        if status and metadata.get("review_status") != status:
            continue
        card_date = str(
            metadata.get("collected_date" if date_basis == "collected" else "date")
            or metadata.get("date", "")
        )
        try:
            parsed_date = date.fromisoformat(card_date)
        except ValueError:
            continue
        if not (start <= parsed_date <= end):
            continue
        sections = extract_sections(card.content)
        title = metadata.get("title_zh") or metadata.get("title_en") or metadata.get("id", path.stem)
        items.append(
            {
                "id": metadata.get("id", path.stem),
                "title": title,
                "title_en": metadata.get("title_en", ""),
                "source_url": metadata.get("source_url", ""),
                "date": str(metadata.get("date", "")),
                "collected_date": str(metadata.get("collected_date", metadata.get("date", ""))),
                "topics": metadata.get("topics", []),
                "entities": metadata.get("entities", []),
                "content": card.content,
                "conclusion": first_available(sections, ["一句话结论"], fallback=""),
                "overview": first_available(
                    sections,
                    ["事件概述", "研究问题", "事件概述 / 研究问题", "事件概述或研究问题"],
                    fallback="",
                ),
            }
        )
    return sorted(items, key=lambda item: (item["date"], item["id"]), reverse=True)


def match_cards_to_nodes(
    cards: list[dict[str, Any]], registered_nodes: list[RegisteredPPTNode], limit_per_card: int = 3
) -> list[PPTCardSuggestion]:
    suggestions = []
    for card in cards:
        scored = [
            score_card_node_match(card, node)
            for node in registered_nodes
        ]
        for suggestion in sorted(scored, key=lambda item: item.score, reverse=True)[:limit_per_card]:
            if suggestion.score >= card_node_threshold(node_lookup=suggestion.node_id, registered_nodes=registered_nodes):
                suggestions.append(suggestion)
    return sorted(suggestions, key=lambda item: (item.node_id, -item.score, item.title))


def card_node_threshold(node_lookup: str, registered_nodes: list[RegisteredPPTNode]) -> int:
    for node in registered_nodes:
        if node.node_id != node_lookup:
            continue
        if node.node_id.startswith("auto.") or node.role == "自动生成节点":
            return 3
        return 4
    return 4


def score_card_node_match(card: dict[str, Any], node: RegisteredPPTNode) -> PPTCardSuggestion:
    text = "\n".join(
        [
            str(card.get("title", "")),
            str(card.get("title_en", "")),
            " ".join(card.get("topics", [])),
            " ".join(card.get("entities", [])),
            str(card.get("conclusion", "")),
            str(card.get("overview", "")),
            str(card.get("content", ""))[:1500],
        ]
    )
    score = 0
    reasons = []
    keyword_hits = matching_terms(text, node.keywords)
    if keyword_hits:
        score += min(len(keyword_hits), 6) * 3
        reasons.append("关键词：" + "、".join(keyword_hits[:6]))
    topic_hits = [topic for topic in card.get("topics", []) if topic in node.keywords or topic in node.text]
    if topic_hits:
        score += min(len(topic_hits), 3) * 4
        reasons.append("主题：" + "、".join(topic_hits[:3]))
    intent_hits = matching_terms(text, [node.intent])
    if intent_hits:
        score += 2
        reasons.append("节点意图")
    return PPTCardSuggestion(
        card_id=str(card.get("id", "")),
        title=str(card.get("title", "")),
        source_url=str(card.get("source_url", "")),
        date=str(card.get("date", "")),
        topics=list(card.get("topics", [])),
        conclusion=str(card.get("conclusion", "")),
        overview=str(card.get("overview", "")),
        node_id=node.node_id,
        node_label=node.title_path or node.node_id,
        score=score,
        reasons=reasons,
    )


def write_ppt_plan(
    markdown_root: Path,
    from_date: str,
    to_date: str,
    date_basis: str,
    status: str,
    node_matches: list[PPTNodeMatch],
    suggestions: list[PPTCardSuggestion],
    section_trends: list[PPTSectionTrendSuggestion] | None = None,
    deck_id: str = "",
    deck_title: str = "",
    deck_version: str = "",
    llm_client: Any | None = None,
) -> Path:
    output_dir = markdown_root / "inbox"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = unique_ppt_plan_path(output_dir, from_date, to_date, deck_id=deck_id)
    lines = [
        f"# PPT 更新建议：{from_date} 至 {to_date}",
        "",
        f"- PPT：{deck_title or deck_id or '未命名'}" + (f"（{deck_version}）" if deck_version else ""),
        f"- 日期口径：{'入库日期' if date_basis == 'collected' else '信息日期'}",
        f"- 卡片状态：{status}",
        f"- 已注册节点：{len(node_matches)}",
        f"- 有建议的节点：{len({item.node_id for item in suggestions})}",
        "- 文字风格：保持与原 PPT 相近，偏口头汇报，不写成论文摘要。",
        "- 时间戳规则：每个结构节点下 2025 年 10 月后的日期尽量不超过 2 个，优先保留最新或最关键节点。",
        "- 小节建议：结合趋势关键词，从二级标题层面提示哪些小节需要调整内容重心或新增三级标题。",
        "",
        "## 节点匹配概览",
        "",
    ]
    for match in node_matches:
        location = match.current.title_path if match.current else "未匹配到当前 PPT 结构"
        pages = ", ".join(str(page) for page in match.current.pages) if match.current else ""
        lines.append(f"- `{match.registered.node_id}` → {location}" + (f"（当前页码：{pages}）" if pages else ""))
    lines.extend(["", "## 二级小节趋势建议", ""])
    if section_trends:
        for item in section_trends:
            pages = f"（页码参考：{', '.join(str(page) for page in item.pages)}）" if item.pages else ""
            trend_text = "、".join(
                f"{trend['label']}×{trend['count']}" for trend in item.trends[:5]
            )
            lines.extend(
                [
                    f"### {item.label}{pages}",
                    "",
                    f"- 相关卡片：{item.card_count} 张",
                    f"- 趋势关键词：{trend_text}",
                    f"- 更新建议：{item.recommendation}",
                    "",
                ]
            )
    else:
        lines.append("暂无可汇总到二级标题的趋势建议。")
        lines.append("")
    lines.extend(["## 结构化更新建议", ""])
    if not suggestions:
        lines.append("暂无符合条件的卡片更新建议。")
    grouped: dict[str, list[PPTCardSuggestion]] = {}
    for suggestion in suggestions:
        grouped.setdefault(suggestion.node_id, []).append(suggestion)
    node_lookup = {match.registered.node_id: match for match in node_matches}
    for node_id, items in grouped.items():
        match = node_lookup.get(node_id)
        registered = match.registered if match else None
        lines.extend(
            [
                f"### {node_id}",
                "",
                f"- 当前结构：{registered.title_path if registered else items[0].node_label}",
                f"- 节点意图：{registered.intent if registered else '未记录'}",
            ]
        )
        if match and match.current and match.current.pages:
            lines.append(f"- 当前页码参考：{', '.join(str(page) for page in match.current.pages)}")
        edits = build_node_concrete_edits(match, registered, items)
        lines.extend(
            [
                "",
                "建议修改：",
                "",
            ]
        )
        for edit in edits:
            target = f"第 {edit['page']} 页" if edit.get("page") else "对应页面"
            original = f"的“{edit['current_text']}”" if edit.get("current_text") else "新增一句"
            lines.extend(
                [
                    f"- {target}{original}可修改为“{edit['suggested_text']}”",
                    f"  - 理由：{edit['rationale']}",
                ]
            )
        lines.extend(
            [
                "",
                "建议口头表述：",
                "",
                f"> {build_oral_update_text(registered, items)}",
                "",
                "建议关注的卡片：",
                "",
            ]
        )
        for item in items[:8]:
            lines.extend(
                [
                    f"#### {item.title}",
                    "",
                    f"- 信息日期：{item.date}",
                    f"- 主题：{', '.join(item.topics) or '未标注'}",
                    f"- 匹配分：{item.score}",
                    f"- 匹配原因：{'; '.join(item.reasons) or '关键词弱匹配'}",
                    f"- 一句话：{item.conclusion or '未提取'}",
                    f"- 事件概述：{item.overview or '未提取'}",
                    f"- 来源：{item.source_url}",
                    "",
                ]
            )
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    write_ppt_plan_json(
        output_path,
        from_date,
        to_date,
        date_basis,
        status,
        node_matches,
        suggestions,
        section_trends or [],
        deck_id=deck_id,
        deck_title=deck_title,
        deck_version=deck_version,
        llm_client=llm_client,
    )
    return output_path


def write_ppt_plan_json(
    markdown_path: Path,
    from_date: str,
    to_date: str,
    date_basis: str,
    status: str,
    node_matches: list[PPTNodeMatch],
    suggestions: list[PPTCardSuggestion],
    section_trends: list[PPTSectionTrendSuggestion],
    deck_id: str = "",
    deck_title: str = "",
    deck_version: str = "",
    llm_client: Any | None = None,
) -> Path:
    node_lookup = {match.registered.node_id: match for match in node_matches}
    grouped: dict[str, list[PPTCardSuggestion]] = {}
    for suggestion in suggestions:
        grouped.setdefault(suggestion.node_id, []).append(suggestion)
    items = []
    for trend in section_trends:
        title = trend.label
        related_suggestions = [item for item in suggestions if item.card_id in set(trend.card_ids)]
        items.append(
            {
                "suggestion_id": ppt_suggestion_id(markdown_path.name, "section_trend", title),
                "kind": "section_trend",
                "kind_label": "小节趋势建议",
                "title": title,
                "location": title,
                "level1": trend.level1,
                "level2": trend.level2,
                "level3": "",
                "pages": trend.pages,
                "recommendation": trend.recommendation,
                "oral_text": "",
                "edits": build_section_trend_edits(trend, related_suggestions),
                "trend_keywords": trend.trends,
                "card_ids": trend.card_ids,
                "cards": cards_for_json(related_suggestions),
            }
        )
    for node_id, node_suggestions in grouped.items():
        match = node_lookup.get(node_id)
        registered = match.registered if match else None
        current = match.current if match else None
        location = (
            current.title_path
            if current
            else registered.title_path if registered else node_suggestions[0].node_label
        )
        title = node_id
        edits = build_node_concrete_edits(match, registered, node_suggestions)
        items.append(
            {
                "suggestion_id": ppt_suggestion_id(markdown_path.name, "node_update", node_id),
                "kind": "node_update",
                "kind_label": "结构节点建议",
                "title": title,
                "node_id": node_id,
                "location": location,
                "level1": current.level1 if current else registered.current_level1 if registered else "",
                "level2": current.level2 if current else registered.current_level2 if registered else "",
                "level3": current.level3 if current else registered.current_level3 if registered else "",
                "pages": current.pages if current else [],
                "recommendation": concrete_edit_summary(edits)
                or build_node_recommendation(registered, node_suggestions),
                "oral_text": build_oral_update_text(registered, node_suggestions),
                "edits": edits,
                "trend_keywords": [],
                "card_ids": unique_card_ids(node_suggestions),
                "cards": cards_for_json(node_suggestions),
            }
        )
    items = build_ppt_update_groups_by_importance(
        items, suggestions, markdown_path.name, llm_client
    )
    items = polish_ppt_items_with_llm(items, llm_client)
    payload = {
        "report_id": markdown_path.stem,
        "report_name": markdown_path.name,
        "markdown_path": str(markdown_path),
        "deck_id": deck_id,
        "deck_title": deck_title,
        "deck_version": deck_version,
        "from_date": from_date,
        "to_date": to_date,
        "date_basis": date_basis,
        "status": status,
        "items": items,
    }
    json_path = markdown_path.with_suffix(".json")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def build_ppt_update_groups_by_importance(
    items: list[dict[str, Any]],
    suggestions: list[PPTCardSuggestion],
    report_name: str,
    llm_client: Any | None = None,
) -> list[dict[str, Any]]:
    passthrough = [item for item in items if not item.get("card_ids")]
    scoped_items = [item for item in items if item.get("card_ids")]
    if not scoped_items:
        return sorted(passthrough, key=lambda item: str(item.get("title", "")))

    card_lookup = {suggestion.card_id: suggestion for suggestion in suggestions}
    all_card_ids = sorted({str(card_id) for item in scoped_items for card_id in item.get("card_ids", [])})
    importance = score_card_importance_with_llm(all_card_ids, card_lookup, llm_client)
    core_ids, auxiliary_ids = select_core_cards(all_card_ids, importance)
    groups = group_core_cards_by_semantics_with_llm(core_ids, card_lookup, scoped_items, llm_client)
    groups = attach_auxiliary_evidence(groups, auxiliary_ids, card_lookup)

    merged_items = [
        build_grouped_ppt_item(group, scoped_items, report_name, index)
        for index, group in enumerate(groups)
    ]
    return sorted(
        [*merged_items, *passthrough],
        key=lambda item: (grouped_item_order(item), str(item.get("title", ""))),
    )


def score_card_importance_with_llm(
    card_ids: list[str],
    card_lookup: dict[str, PPTCardSuggestion],
    llm_client: Any | None,
) -> dict[str, int]:
    if llm_client and getattr(llm_client, "available", False):
        prompt = build_card_importance_prompt(card_ids, card_lookup)
        try:
            content = llm_client.generate_card_content(prompt)
        except Exception:
            content = None
        parsed = parse_card_importance_response(content)
        if parsed:
            scores = {card_id: parsed.get(card_id, 0) for card_id in card_ids}
            if any(scores.values()):
                return scores
    return fallback_card_importance(card_ids, card_lookup)


def build_card_importance_prompt(card_ids: list[str], card_lookup: dict[str, PPTCardSuggestion]) -> str:
    payload = {
        "cards": [
            {
                "card_id": card_id,
                "title": card_lookup[card_id].title,
                "topics": card_lookup[card_id].topics,
                "conclusion": card_lookup[card_id].conclusion,
                "overview": card_lookup[card_id].overview,
            }
            for card_id in card_ids
            if card_id in card_lookup
        ]
    }
    return (
        "你是中文 AI 行业与技术前沿分析师。请为下面这些知识卡片打重要性分（1-5 分，"
        "5 分表示对讲稿最重要、最值得优先讲述，1 分表示边缘信息，可作为辅助证据）。\n"
        "要求：\n"
        "1. 只输出 JSON，不要 Markdown，不要解释。\n"
        "2. 输出格式为 {\"scores\":[{\"card_id\":\"...\",\"score\":1-5}]}。\n"
        "3. 每张卡片都要给分，不要遗漏。\n"
        "4. 判断依据：对行业/技术趋势的代表性、影响范围、时效性。\n\n"
        f"输入 JSON：\n{json.dumps(payload, ensure_ascii=False)}"
    )


def parse_card_importance_response(content: str | None) -> dict[str, int] | None:
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
    if not isinstance(parsed, dict) or not isinstance(parsed.get("scores"), list):
        return None
    scores = {}
    for entry in parsed["scores"]:
        card_id = str(entry.get("card_id", ""))
        try:
            score = int(entry.get("score", 0))
        except (TypeError, ValueError):
            continue
        if card_id:
            scores[card_id] = max(1, min(5, score))
    return scores or None


def fallback_card_importance(card_ids: list[str], card_lookup: dict[str, PPTCardSuggestion]) -> dict[str, int]:
    return {card_id: card_lookup[card_id].score if card_id in card_lookup else 0 for card_id in card_ids}


def select_core_cards(
    card_ids: list[str], importance: dict[str, int], min_count: int = 18, max_count: int = 24
) -> tuple[list[str], list[str]]:
    ranked = sorted(card_ids, key=lambda card_id: (-importance.get(card_id, 0), card_id))
    if len(ranked) <= min_count:
        return ranked, []
    core_count = min(max_count, len(ranked))
    cutoff_score = importance.get(ranked[min_count - 1], 0)
    while core_count > min_count and importance.get(ranked[core_count - 1], 0) < cutoff_score:
        core_count -= 1
    while core_count < len(ranked) and core_count < max_count and importance.get(ranked[core_count], 0) >= cutoff_score:
        core_count += 1
    core_count = min(core_count, max_count, len(ranked))
    return ranked[:core_count], ranked[core_count:]


def group_core_cards_by_semantics_with_llm(
    core_ids: list[str],
    card_lookup: dict[str, PPTCardSuggestion],
    scoped_items: list[dict[str, Any]],
    llm_client: Any | None,
) -> list[dict[str, Any]]:
    if not core_ids:
        return []
    if llm_client and getattr(llm_client, "available", False):
        prompt = build_semantic_grouping_prompt(core_ids, card_lookup)
        try:
            content = llm_client.generate_card_content(prompt)
        except Exception:
            content = None
        parsed_groups = parse_semantic_grouping_response(content, set(core_ids))
        if parsed_groups:
            return parsed_groups
    return group_core_cards_by_structure(core_ids, scoped_items)


def build_semantic_grouping_prompt(core_ids: list[str], card_lookup: dict[str, PPTCardSuggestion]) -> str:
    payload = {
        "cards": [
            {
                "card_id": card_id,
                "title": card_lookup[card_id].title,
                "topics": card_lookup[card_id].topics,
                "conclusion": card_lookup[card_id].conclusion,
            }
            for card_id in core_ids
            if card_id in card_lookup
        ]
    }
    return (
        "你是中文 PPT 讲稿编辑。请把下面这些核心知识卡片按含义/意义是否高度重合进行分组，"
        "只有当多张卡片讲的其实是同一件事、同一个模型/同一个结论时才合并为一组；"
        "只是话题相关或领域相邻，但具体事件、模型、结论不同的卡片，应该分成不同组。\n"
        "要求：\n"
        "1. 只输出 JSON，不要 Markdown，不要解释。\n"
        "2. 输出格式为 {\"groups\":[{\"card_ids\":[\"...\"],\"label\":\"分组主题\"}]}。\n"
        "3. 每张卡片必须且只能出现在一个分组中。\n"
        "4. 优先保持细粒度分组：宁可分得多、分得细，也不要把不完全是同一件事的卡片合并到一起；"
        "每组原则上不超过 2-3 张卡片，除非它们确实是对同一事件/同一模型的重复报道。\n"
        "5. 不确定是否高度重合时，应该分为不同组，而不是合并。\n\n"
        f"输入 JSON：\n{json.dumps(payload, ensure_ascii=False)}"
    )


def parse_semantic_grouping_response(
    content: str | None, valid_ids: set[str]
) -> list[dict[str, Any]] | None:
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
    if not isinstance(parsed, dict) or not isinstance(parsed.get("groups"), list):
        return None
    groups = []
    seen: set[str] = set()
    for entry in parsed["groups"]:
        card_ids = [str(card_id) for card_id in entry.get("card_ids", []) if str(card_id) in valid_ids]
        card_ids = [card_id for card_id in card_ids if card_id not in seen]
        if not card_ids:
            continue
        seen.update(card_ids)
        groups.append({"card_ids": card_ids, "label": str(entry.get("label") or "")})
    missing = [card_id for card_id in valid_ids if card_id not in seen]
    if missing:
        groups.append({"card_ids": sorted(missing), "label": ""})
    return groups or None


def group_core_cards_by_structure(
    core_ids: list[str], scoped_items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    node_items = [item for item in scoped_items if item.get("kind") == "node_update"]
    card_to_node: dict[str, str] = {}
    for item in node_items:
        node_key = str(item.get("node_id") or item.get("title") or item.get("suggestion_id"))
        for card_id in item.get("card_ids", []):
            card_to_node.setdefault(str(card_id), node_key)
    buckets: dict[str, list[str]] = {}
    for card_id in core_ids:
        key = card_to_node.get(card_id, card_id)
        buckets.setdefault(key, []).append(card_id)
    return [{"card_ids": card_ids, "label": ""} for card_ids in buckets.values()]


def attach_auxiliary_evidence(
    groups: list[dict[str, Any]],
    auxiliary_ids: list[str],
    card_lookup: dict[str, PPTCardSuggestion],
) -> list[dict[str, Any]]:
    if not groups:
        return groups
    for card_id in auxiliary_ids:
        card = card_lookup.get(card_id)
        best_index = -1
        best_score = 0
        for index, group in enumerate(groups):
            overlap = keyword_overlap_score(card, group["card_ids"], card_lookup)
            if overlap > best_score:
                best_score = overlap
                best_index = index
        if best_index >= 0:
            groups[best_index]["card_ids"].append(card_id)
    return groups


def keyword_overlap_score(
    card: PPTCardSuggestion | None, group_card_ids: list[str], card_lookup: dict[str, PPTCardSuggestion]
) -> float:
    if not card or not group_card_ids:
        return 0.0
    card_topics = set(card.topics)
    total = 0
    counted = 0
    for group_card_id in group_card_ids:
        group_card = card_lookup.get(group_card_id)
        if not group_card:
            continue
        counted += 1
        if group_card.node_id == card.node_id:
            total += 2
        total += len(card_topics & set(group_card.topics))
    return total / counted if counted else 0.0


def build_grouped_ppt_item(
    group: dict[str, Any],
    scoped_items: list[dict[str, Any]],
    report_name: str,
    index: int,
) -> dict[str, Any]:
    card_ids = list(dict.fromkeys(group["card_ids"]))
    member_items = [
        item for item in scoped_items if set(item.get("card_ids", [])) & set(card_ids)
    ]
    if len(member_items) == 1:
        primary = dict(member_items[0])
        primary["card_ids"] = card_ids
        primary["cards"] = [
            card for card in primary.get("cards", []) if str(card.get("card_id")) in card_ids
        ] or primary.get("cards", [])
        return primary

    primary = select_primary_ppt_item(member_items) if member_items else {}
    locations = unique_ppt_locations([ppt_target_location(item) for item in member_items])
    pages = sorted({page for item in member_items for page in item.get("pages", []) if page})
    all_cards = []
    seen_card_ids = set()
    for item in member_items:
        for card in item.get("cards", []):
            card_id = str(card.get("card_id"))
            if card_id in seen_card_ids or card_id not in card_ids:
                continue
            seen_card_ids.add(card_id)
            all_cards.append(card)
    label = str(group.get("label") or primary.get("title") or "合并更新建议")
    merged = dict(primary)
    merged["suggestion_id"] = ppt_suggestion_id(report_name, "importance_group", f"{index}:{'|'.join(card_ids)}")
    merged["kind"] = "merged_update"
    merged["kind_label"] = "合并更新建议"
    merged["title"] = label
    merged["location"] = str(primary.get("location", ""))
    merged["pages"] = pages
    merged["card_ids"] = card_ids
    merged["cards"] = all_cards
    merged["target_locations"] = locations
    merged["recommendation"] = merged_recommendation(primary, locations)
    merged["edits"] = merge_item_edits(primary, locations)
    return merged


def unique_ppt_locations(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique = []
    seen = set()
    for location in locations:
        key = (
            str(location.get("location") or location.get("title") or ""),
            tuple(str(page) for page in location.get("pages", []) or []),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(location)
    return unique


def select_primary_ppt_item(group: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        group,
        key=lambda item: (
            0 if item.get("kind") == "section_trend" else 1,
            min(item.get("pages", [9999]) or [9999]),
            str(item.get("title", "")),
        ),
    )[0]


def ppt_target_location(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": item.get("title", ""),
        "kind": item.get("kind", ""),
        "kind_label": item.get("kind_label", item.get("kind", "")),
        "location": item.get("location", ""),
        "level1": item.get("level1", ""),
        "level2": item.get("level2", ""),
        "level3": item.get("level3", ""),
        "pages": item.get("pages", []),
        "instruction": ((item.get("edits") or [{}])[0]).get("instruction", ""),
    }


def merged_recommendation(primary: dict[str, Any], locations: list[dict[str, Any]]) -> str:
    recommendation = str(primary.get("recommendation") or "")
    if len(locations) <= 1:
        return recommendation
    return f"{recommendation}（同一更新还匹配到 {len(locations) - 1} 个相近位置，建议选择一个主位置写入。）"


def merge_item_edits(primary: dict[str, Any], locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edits = [dict(edit) for edit in primary.get("edits", [])]
    if not edits:
        return edits
    edit = edits[0]
    page = edit.get("page") or ((locations[0].get("pages") or [None])[0])
    location_text = location_label(locations[0])
    alternatives = [location_label(item) for item in locations[1:]]
    if alternatives:
        edit["instruction"] = (
            f"建议优先放在{page_label(page)}“{location_text}”。"
            f"同一更新也匹配到：{'；'.join(alternatives[:4])}。"
            "为避免重复写入，请选择一个主位置，其余位置只在需要时交叉引用。"
        )
    edit["target_locations"] = locations
    edits[0] = edit
    return edits


def location_label(location: dict[str, Any]) -> str:
    text = str(location.get("location") or location.get("title") or "对应小节")
    return clean_heading(text.split(" / ")[-1])


def page_label(page: Any) -> str:
    return f"第 {page} 页" if page else "对应页面"


def grouped_item_order(item: dict[str, Any]) -> tuple[int, int]:
    pages = item.get("pages", []) or [9999]
    kind = item.get("kind", "")
    if kind == "merged_update":
        rank = 0
    elif kind == "section_trend":
        rank = 1
    else:
        rank = 2
    return rank, min(pages) if pages else 9999


def polish_ppt_items_with_llm(items: list[dict[str, Any]], llm_client: Any | None) -> list[dict[str, Any]]:
    if not items or not llm_client or not getattr(llm_client, "available", False):
        return items
    prompt = build_ppt_polish_prompt(items)
    try:
        content = llm_client.generate_card_content(prompt)
    except Exception:
        return items
    polished = parse_ppt_polish_response(content)
    if not polished:
        return items
    polished_by_id = {
        str(item.get("suggestion_id", "")): item
        for item in polished.get("items", [])
        if item.get("suggestion_id")
    }
    updated_items = []
    for item in items:
        replacement = polished_by_id.get(str(item.get("suggestion_id", "")))
        if not replacement or not item.get("edits"):
            updated_items.append(item)
            continue
        edit = dict(item["edits"][0])
        for key in ["instruction", "suggested_text", "rationale"]:
            value = str(replacement.get(key, "")).strip()
            if value:
                edit[key] = value
        updated = dict(item)
        updated["edits"] = [edit, *item["edits"][1:]]
        if edit.get("suggested_text"):
            updated["recommendation"] = edit["suggested_text"]
        updated_items.append(updated)
    return updated_items


def build_ppt_polish_prompt(items: list[dict[str, Any]], max_items: int = 20) -> str:
    payload = {"items": [ppt_polish_prompt_item(item) for item in items[:max_items]]}
    return (
        "你是中文 PPT 讲稿更新编辑。请把下面的自动建议改写成更具体、可操作、适合口头汇报的改稿建议。\n"
        "要求：\n"
        "1. 只输出 JSON，不要 Markdown，不要解释。\n"
        "2. 输出格式为 {\"items\":[{\"suggestion_id\":\"...\",\"instruction\":\"...\",\"suggested_text\":\"...\",\"rationale\":\"...\"}]}。\n"
        "3. instruction 必须说明第几页、放在小节哪里、是否改标题。\n"
        "4. suggested_text 只写可直接放入讲稿或口播的话，不要把标题和操作说明混进去。\n"
        "5. suggested_text 保持口头汇报风格，中文自然，尽量 80 到 160 字。\n"
        "6. 每条建议最多保留 2 个 2025 年 10 月后的具体日期；没有必要就不写日期。\n"
        "7. 不要编造证据卡片之外的事实。\n\n"
        f"输入 JSON：\n{json.dumps(payload, ensure_ascii=False)}"
    )


def ppt_polish_prompt_item(item: dict[str, Any]) -> dict[str, Any]:
    edit = (item.get("edits") or [{}])[0]
    cards = []
    for card in item.get("cards", [])[:3]:
        cards.append(
            {
                "title": card.get("title", ""),
                "date": card.get("date", ""),
                "conclusion": card.get("conclusion", ""),
                "overview": card.get("overview", ""),
            }
        )
    return {
        "suggestion_id": item.get("suggestion_id", ""),
        "kind_label": item.get("kind_label", ""),
        "location": item.get("location", ""),
        "pages": item.get("pages", []),
        "current_text": edit.get("current_text", ""),
        "rule_instruction": edit.get("instruction", ""),
        "rule_suggested_text": edit.get("suggested_text", item.get("recommendation", "")),
        "evidence_cards": cards,
    }


def parse_ppt_polish_response(content: str | None) -> dict[str, Any] | None:
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
    if not isinstance(parsed, dict) or not isinstance(parsed.get("items"), list):
        return None
    return parsed


def ppt_suggestion_id(report_name: str, kind: str, title: str) -> str:
    return hashlib.sha1(f"{report_name}|{kind}|{title}".encode("utf-8")).hexdigest()[:16]


def unique_card_ids(suggestions: list[PPTCardSuggestion]) -> list[str]:
    card_ids = []
    seen = set()
    for suggestion in suggestions:
        if suggestion.card_id in seen:
            continue
        seen.add(suggestion.card_id)
        card_ids.append(suggestion.card_id)
    return card_ids


def cards_for_json(suggestions: list[PPTCardSuggestion]) -> list[dict[str, Any]]:
    cards = []
    seen = set()
    for item in suggestions:
        if item.card_id in seen:
            continue
        seen.add(item.card_id)
        cards.append(
            {
                "card_id": item.card_id,
                "title": item.title,
                "date": item.date,
                "topics": item.topics,
                "source_url": item.source_url,
                "conclusion": item.conclusion,
                "overview": item.overview,
                "score": item.score,
                "reasons": item.reasons,
            }
        )
    return cards


def build_node_recommendation(node: Any, suggestions: list[PPTCardSuggestion]) -> str:
    if not suggestions:
        return "本节点暂无新的更新建议。"
    top = sorted(suggestions, key=lambda item: item.score, reverse=True)[0]
    summary = top.conclusion or top.overview or top.title
    return compact_sentence(summary, max_chars=96)


def build_node_concrete_edits(
    match: PPTNodeMatch | None,
    node: Any,
    suggestions: list[PPTCardSuggestion],
    max_edits: int = 1,
) -> list[dict[str, Any]]:
    if not suggestions:
        return []
    current = match.current if match else None
    pages = current.pages if current else []
    current_text = select_current_text_excerpt(current) if current else ""
    oral_text = build_oral_update_text(node, suggestions)
    suggested_text = build_replacement_text(current_text, oral_text)
    top = sorted(suggestions, key=lambda item: item.score, reverse=True)[0]
    rationale = top.conclusion or top.overview or top.title
    return [
        {
            "type": "replace" if current_text else "append",
            "type_label": "建议替换原文" if current_text else "建议新增一段",
            "instruction": build_node_edit_instruction(current, current_text),
            "page": pages[0] if pages else None,
            "pages": pages,
            "current_text": current_text,
            "suggested_text": suggested_text,
            "rationale": compact_sentence(rationale, max_chars=110),
            "card_ids": unique_card_ids(suggestions[:max_edits + 3]),
        }
    ]


def build_section_trend_edits(
    trend: PPTSectionTrendSuggestion, suggestions: list[PPTCardSuggestion] | None = None
) -> list[dict[str, Any]]:
    page = trend.pages[0] if trend.pages else None
    trend_labels = "、".join(str(item["label"]) for item in trend.trends[:3])
    section_name = clean_heading(trend.level2) or "本小节"
    suggested_text = build_section_oral_text(section_name, trend_labels, suggestions or [])
    instruction = (
        f"在第 {page} 页“{section_name}”小节末尾新增一个“近期变化”口播点，不改小节标题。"
        if page
        else f"在“{section_name}”小节末尾新增一个“近期变化”口播点，不改小节标题。"
    )
    return [
        {
            "type": "append",
            "type_label": "建议新增一段",
            "instruction": instruction,
            "page": page,
            "pages": trend.pages,
            "current_text": "",
            "suggested_text": compact_sentence(suggested_text, max_chars=170),
            "rationale": f"该小节近期匹配到 {trend.card_count} 张相关卡片。",
            "card_ids": trend.card_ids,
        }
    ]


def build_node_edit_instruction(current: Any, current_text: str) -> str:
    page = current.pages[0] if current and current.pages else None
    level3 = clean_heading(current.level3) if current else ""
    target = f"第 {page} 页" if page else "对应页面"
    section = f"“{level3}”" if level3 else "当前小节"
    if current_text:
        return f"检查{target}{section}的现有表述，保留原结构，把下方文字作为替换后的口播稿。"
    return f"在{target}{section}末尾补充下方口播稿，不单独新增章节。"


def build_section_oral_text(
    section_name: str, trend_labels: str, suggestions: list[PPTCardSuggestion]
) -> str:
    points = []
    seen = set()
    for item in sorted(suggestions, key=lambda suggestion: suggestion.score, reverse=True):
        point = build_card_case_point(item)
        if not point or point in seen:
            continue
        seen.add(point)
        points.append(point)
        if len(points) >= 2:
            break
    landing = build_section_landing_text(section_name, trend_labels)
    if len(points) >= 2:
        return (
            f"这里建议补充两个近期案例：第一，{points[0]}，用作{section_name}从概念走向具体场景的案例；"
            f"第二，{points[1]}，用作{section_name}安全性和行为一致性讨论的案例。{landing}"
        )
    if points:
        return f"这里建议补充一个近期案例：{points[0]}，用作{section_name}从概念走向具体场景的案例。{landing}"
    if trend_labels:
        return f"这里建议补一个近期案例或图示。{landing}"
    return f"这里建议补一个近期案例或图示，作为{section_name}的口播更新点。"


def build_card_case_point(item: PPTCardSuggestion) -> str:
    return compact_sentence(item.title or item.conclusion or item.overview, max_chars=34)


def build_section_landing_text(section_name: str, trend_labels: str) -> str:
    focus = remove_repeated_focus(section_name, trend_labels)
    if focus:
        return f"讲稿落点可以收束为：{section_name}正在从概念介绍转向{focus}等更具体的案例和评估。"
    return f"讲稿落点可以收束为：{section_name}正在从概念介绍转向更具体的案例和评估。"


def remove_repeated_focus(section_name: str, trend_labels: str) -> str:
    labels = [label for label in trend_labels.split("、") if label and label != section_name]
    return "、".join(labels[:3])


def concrete_edit_summary(edits: list[dict[str, Any]]) -> str:
    if not edits:
        return ""
    edit = edits[0]
    target = f"第 {edit['page']} 页" if edit.get("page") else "对应页面"
    if edit.get("current_text"):
        return f"{target}的“{edit['current_text']}”可修改为“{edit['suggested_text']}”"
    return f"{target}可新增表述：“{edit['suggested_text']}”"


def select_current_text_excerpt(current: Any, max_chars: int = 92) -> str:
    if not current:
        return ""
    candidates = [
        *getattr(current, "content", []),
        *getattr(current, "circled_items", []),
        *getattr(current, "figure_notes", []),
    ]
    for candidate in candidates:
        text = compact_sentence(str(candidate), max_chars=max_chars)
        if text:
            return text
    return ""


def build_replacement_text(current_text: str, oral_text: str, max_chars: int = 190) -> str:
    oral = compact_sentence(oral_text, max_chars=130)
    if not current_text:
        return oral
    base = compact_sentence(current_text, max_chars=72)
    if oral and oral not in base:
        return compact_sentence(f"{base}。{oral}", max_chars=max_chars)
    return compact_sentence(base, max_chars=max_chars)


def summarize_level2_trends(
    node_matches: list[PPTNodeMatch],
    suggestions: list[PPTCardSuggestion],
    topics_config: dict[str, Any],
    max_trends_per_section: int = 5,
) -> list[PPTSectionTrendSuggestion]:
    if not suggestions:
        return []
    node_lookup = {match.registered.node_id: match for match in node_matches}
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for suggestion in suggestions:
        match = node_lookup.get(suggestion.node_id)
        level1, level2, pages = level2_location(match)
        key = (level1, level2)
        bucket = buckets.setdefault(
            key,
            {
                "level1": level1,
                "level2": level2,
                "pages": set(),
                "card_texts": {},
            },
        )
        bucket["pages"].update(pages)
        bucket["card_texts"].setdefault(
            suggestion.card_id,
            "\n".join(
                [suggestion.title, " ".join(suggestion.topics), suggestion.conclusion, suggestion.overview]
            )
        )

    sections: list[PPTSectionTrendSuggestion] = []
    groups = trend_term_groups(topics_config)
    for bucket in buckets.values():
        text = "\n".join(bucket["card_texts"].values())
        trends = []
        for group in groups:
            count = trend_group_count(text, group["terms"])
            if count:
                trends.append(
                    {
                        "id": group["id"],
                        "label": group["label"],
                        "count": count,
                        "aliases": group.get("aliases", []),
                        "configured": group.get("configured", False),
                    }
                )
        if not trends:
            continue
        top_trends = sorted(trends, key=lambda item: (item["count"], item["label"]), reverse=True)[
            :max_trends_per_section
        ]
        sections.append(
            PPTSectionTrendSuggestion(
                level1=bucket["level1"],
                level2=bucket["level2"],
                pages=sorted(bucket["pages"]),
                card_ids=sorted(bucket["card_texts"]),
                card_count=len(bucket["card_texts"]),
                trends=top_trends,
                recommendation=build_level2_trend_recommendation(bucket["level2"], top_trends),
            )
        )
    return sorted(sections, key=lambda item: (-item.card_count, item.level1, item.level2))


def level2_location(match: PPTNodeMatch | None) -> tuple[str, str, list[int]]:
    if match and match.current:
        return match.current.level1, match.current.level2, match.current.pages
    if match:
        return match.registered.current_level1, match.registered.current_level2, []
    return "", "", []


def build_level2_trend_recommendation(level2: str, trends: list[dict[str, Any]]) -> str:
    labels = [str(item["label"]) for item in trends[:3]]
    if not labels:
        return "本小节暂不需要明显调整，可等待更多材料后再更新。"
    focus = "、".join(labels)
    section_name = clean_heading(level2) or "本小节"
    return f"{section_name}可围绕{focus}补充近期变化，优先更新对应三级标题下的案例、图示和口头表述。"


def clean_heading(text: str) -> str:
    return re.sub(r"^[（(]?[一二三四五六七八九十]+[）)]?", "", text).strip()


def build_oral_update_text(
    node: Any, suggestions: list[PPTCardSuggestion], max_recent_dates: int = 2
) -> str:
    if not suggestions:
        return "本节暂无新的更新材料，可保留当前表述。"
    top_items = sorted(suggestions, key=lambda item: item.score, reverse=True)[:2]
    date_labels = recent_date_labels(top_items, max_recent_dates=max_recent_dates)
    lead = oral_node_lead(node)
    clauses = []
    for index, item in enumerate(top_items):
        date_prefix = ""
        if item.date in date_labels:
            date_prefix = f"{item.date}，"
        summary = item.conclusion or item.overview or item.title
        clauses.append(f"{date_prefix}{item.title}：{compact_sentence(summary, max_chars=64)}")
    return f"{lead}{'；'.join(clauses)}。"


def oral_node_lead(node: Any) -> str:
    if not node:
        return "这一部分可以补充说明："
    if "产业" in node.role:
        return "这一部分可以补充几个最新产业信号："
    if "技术" in node.role:
        return "这一部分可以强调技术演进的新变化："
    if "理论" in node.role:
        return "这一部分可以补充前沿模型能力的新进展："
    return "这一部分可以补充说明："


def recent_date_labels(
    suggestions: list[PPTCardSuggestion], max_recent_dates: int = 2
) -> set[str]:
    threshold = date(2025, 10, 1)
    parsed: list[date] = []
    for item in suggestions:
        try:
            parsed_date = date.fromisoformat(item.date)
        except ValueError:
            continue
        if parsed_date >= threshold:
            parsed.append(parsed_date)
    return {item.isoformat() for item in sorted(set(parsed), reverse=True)[:max_recent_dates]}


def compact_sentence(text: str, max_chars: int = 96) -> str:
    compact = re.sub(r"\s+", " ", text).strip().rstrip("。；;")
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip("，,；;。") + "…"


def unique_ppt_plan_path(output_dir: Path, from_date: str, to_date: str, deck_id: str = "") -> Path:
    deck_part = f"_{deck_id}" if deck_id else ""
    base = output_dir / f"{from_date}_to_{to_date}{deck_part}_ppt-update-plan.md"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = output_dir / f"{from_date}_to_{to_date}{deck_part}_ppt-update-plan-{index}.md"
        if not candidate.exists():
            return candidate
        index += 1

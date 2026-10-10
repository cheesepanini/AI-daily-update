"""Reviewed textbook knowledge used by the public learning experience."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai_daily_update.processors.retrieval import title_terms


PRESET_GOALS = {
    "news": ("读懂 AI 新闻", ["人工智能三大流派", "技术成熟度曲线", "模型幻觉与发展挑战"]),
    "use-llm": ("有效使用大模型", ["提示工程与思维链", "大语言模型实践", "模型幻觉与发展挑战"]),
    "build-ai": ("入门 AI 开发", ["人工智能学习三要素", "训练验证推理闭环", "AI开发环境", "统计学习实践"]),
}

def load_catalog(root: Path) -> dict[str, Any]:
    path = root / "content" / "learning" / "catalog.json"
    if not path.is_file():
        return {"complete": False, "items": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError("Invalid learning catalog")
    # A hand-edited catalog must not bypass the editorial gate.
    if any(
        not isinstance(item, dict)
        or item.get("review_status") != "reviewed"
        or not item.get("reviewed_by")
        or not item.get("reviewed_at")
        for item in data["items"]
    ):
        data["complete"] = False
    data["items"] = [
        item for item in data["items"]
        if isinstance(item, dict)
        and item.get("review_status") == "reviewed"
        and item.get("reviewed_by")
        and item.get("reviewed_at")
    ]
    ids = [item.get("id") for item in data["items"]]
    if any(not isinstance(item_id, str) or not item_id for item_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("Invalid learning catalog IDs")
    return data


def item_by_id(catalog: dict[str, Any], item_id: str) -> dict[str, Any] | None:
    return next((item for item in catalog["items"] if item["id"] == item_id), None)


def search_items(catalog: dict[str, Any], query: str, limit: int = 8, kind: str = "") -> list[dict[str, Any]]:
    query = query.strip().lower()
    if not query:
        return []
    terms = title_terms(query)
    scored = []
    for item in catalog["items"]:
        if kind and item["type"] != kind:
            continue
        title = str(item["title"]).lower()
        aliases = [str(alias).lower() for alias in item.get("aliases", [])]
        heading = " ".join([title, *aliases])
        overlap = len(terms & title_terms(heading))
        question_overlap = len(terms & title_terms(str(item.get("question", "")).lower()))
        exact = any(alias and alias in query for alias in [title, *aliases])
        if overlap < 2 and not exact and question_overlap < 3:
            continue
        score = overlap * 3 + min(question_overlap, 12) + (8 if exact else 0)
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    return [item for _, item in scored[:limit]]


def choose_news_concepts_with_llm(catalog: dict[str, Any], metadata: dict[str, Any], content: str, llm: Any) -> list[str] | None:
    """Return reviewed textbook item IDs, [] for no fit, or None when matching failed."""
    if not getattr(llm, "available", False) or not catalog.get("complete"):
        return None
    concepts = {item["id"]: item for item in catalog["items"] if item["type"] in {"concept", "microtopic"}}
    choices = "\n".join(
        f"{item_id} | {item['title']} | {item.get('explanation', '')[:80 if item['type'] == 'concept' else 40]}"
        for item_id, item in concepts.items()
    )
    prompt = (
        "你正在为刚抓取的新闻卡片关联《人工智能导论》教材知识点。"
        "从概念和细知识点中选择读懂新闻所需的基础知识，最多 3 个；优先选择能解释新闻中具体技术的条目，不要求新闻与教材标题用词相同。"
        "先看标题、一句话结论和方法/产品要点中的主事件。若主事件不是 AI，只在后文提到可能与 AI 或脑机接口有关，应返回 []；不要为凑满 3 个而硬选。"
        "涉及模型、智能体、机器人、多模态、生成、部署、AI 安全或行业落地时，尽量选出至少 1 个直接相关知识点。"
        "知识点仅用于解释卡片中的术语，不代表新闻事实已经核实；正文标注待核实时仍可匹配明确出现的技术概念。"
        "纯融资、人事、航天或投稿政策等没有可解释技术内容的消息返回 []，不要硬凑。"
        "只能从列表选 ID，只返回 JSON 字符串数组，不要解释。\n"
        f"标题：{metadata.get('title_zh') or metadata.get('title_en', '')}\n"
        f"正文：{content[:4000]}\n可选教材知识点：\n{choices}"
    )
    try:
        response = llm.generate_card_content(prompt) or ""
        match = re.search(r"\[[\s\S]*?\]", response)
        selected = json.loads(match.group(0)) if match else None
    except Exception:
        return None
    if not isinstance(selected, list) or any(not isinstance(item_id, str) for item_id in selected):
        return None
    titles: dict[str, str | None] = {}
    for item_id, item in concepts.items():
        title = item["title"]
        titles[title] = item_id if title not in titles else None
    ids = list(dict.fromkeys(
        item_id for value in selected
        if (item_id := value if value in concepts else titles.get(value)) is not None
    ))[:3]
    return ids if ids or not selected else None


def plan_for_targets(catalog: dict[str, Any], target_ids: list[str], known_ids: list[str] | None = None) -> list[dict[str, Any]]:
    concepts = {item["id"]: item for item in catalog["items"] if item["type"] == "concept"}
    known = set(known_ids or [])
    ordered: list[dict[str, Any]] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(item_id: str, reason: str) -> None:
        if item_id in visited or item_id in known:
            return
        if item_id in active:
            raise ValueError("Required prerequisite cycle")
        item = concepts.get(item_id)
        if item is None:
            raise ValueError(f"Unknown concept: {item_id}")
        active.add(item_id)
        for prerequisite in item.get("prerequisites", {}).get("required", []):
            visit(prerequisite, f"理解 {item['title']} 的基础主题")
        active.remove(item_id)
        visited.add(item_id)
        ordered.append({"id": item_id, "title": item["title"], "reason": reason})

    for target in target_ids:
        visit(target, "目标主题")
    return ordered


def preset_plan(catalog: dict[str, Any], goal_id: str, known_ids: list[str] | None = None) -> dict[str, Any]:
    title, names = PRESET_GOALS[goal_id]
    concepts = {item["title"]: item["id"] for item in catalog["items"] if item["type"] == "concept"}
    targets = [concepts[name] for name in names if name in concepts]
    if not targets:
        return {"title": title, "steps": [], "message": "该目标的教材内容尚未审核发布。"}
    return {"title": title, "steps": plan_for_targets(catalog, targets, known_ids), "message": ""}


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: item.get(key) for key in (
        "id", "type", "title", "aliases", "source_section", "explanation",
        "example", "misconception", "question", "answer", "prerequisites",
    )}

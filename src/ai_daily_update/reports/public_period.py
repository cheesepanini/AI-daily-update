from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


FIRST_DAY = date(2026, 7, 1)


def source_hash(cards: list[dict[str, Any]]) -> str:
    payload = [
        {
            "id": card["id"],
            "event_date": card["event_date"],
            "title": card["title"],
            "body_hash": card.get("body_hash") or hashlib.sha256(
                card.get("search_fields", {}).get("body", "").encode()
            ).hexdigest(),
            "source_url": card.get("source_url", ""),
            "topics": card.get("topics", []),
            "event_group_id": card.get("event_group_id", ""),
            "other_sources": sorted(item["id"] for item in card.get("other_sources", [])),
        }
        for card in sorted(cards, key=lambda item: item["id"])
    ]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def report_path(markdown_root: Path, period: str, start: date) -> Path:
    return markdown_root / "public_reports" / period / f"{start.isoformat()}.json"


def failure_path(markdown_root: Path, period: str, start: date) -> Path:
    return report_path(markdown_root, period, start).with_suffix(".failure.json")


def failed_report(markdown_root: Path, period: str, start: date, cards: list[dict[str, Any]]) -> bool:
    try:
        data = json.loads(failure_path(markdown_root, period, start).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and data.get("source_hash") == source_hash(cards)


def write_failure(markdown_root: Path, period: str, start: date, cards: list[dict[str, Any]]) -> None:
    path = failure_path(markdown_root, period, start)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source_hash": source_hash(cards)}), encoding="utf-8")


def valid_report(data: Any, cards: list[dict[str, Any]]) -> bool:
    if not isinstance(data, dict) or not isinstance(data.get("lead"), str):
        return False
    if not data["lead"].strip() or len(data["lead"]) > 600:
        return False
    highlights = data.get("highlights")
    watch = data.get("watch")
    if not isinstance(highlights, list) or not min(3, len(cards)) <= len(highlights) <= 5:
        return False
    if not isinstance(watch, list) or len(watch) > 3:
        return False
    allowed = {card["id"] for card in cards}
    for entry in [*highlights, *watch]:
        if not isinstance(entry, dict) or not isinstance(entry.get("text"), str):
            return False
        if not entry["text"].strip() or len(entry["text"]) > 500:
            return False
        ids = entry.get("card_ids")
        if not isinstance(ids, list) or not 1 <= len(ids) <= 4:
            return False
        if any(not isinstance(card_id, str) or card_id not in allowed for card_id in ids):
            return False
    return True


def read_report(markdown_root: Path, period: str, start: date, cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    path = report_path(markdown_root, period, start)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("source_hash") != source_hash(cards) or not valid_report(data, cards):
        return None
    by_id = {card["id"]: card for card in cards}
    for entry in [*data["highlights"], *data["watch"]]:
        entry["sources"] = [by_id[card_id] for card_id in dict.fromkeys(entry["card_ids"])]
    return data


def write_report(markdown_root: Path, period: str, start: date, data: dict[str, Any]) -> Path:
    path = report_path(markdown_root, period, start)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)
    return path


def _model_json(llm: Any, prompt: str, valid: Callable[[Any], bool]) -> Any:
    for attempt in range(2):
        request = prompt
        if attempt:
            instructions, payload = prompt.rsplit("\n", 1)
            request = instructions + "\n上次格式或引用无效。请只输出严格 JSON，并仅引用输入 ID。\n" + payload
        content = llm.generate_card_content(request)
        if not content:
            continue
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
        try:
            data = json.loads(text)
        except ValueError:
            continue
        if valid(data):
            return data
    raise ValueError("AI 未返回证据引用有效的 JSON")


def _day_notes(markdown_root: Path, day: str, cards: list[dict[str, Any]], llm: Any) -> list[dict[str, Any]]:
    path = markdown_root / "public_reports" / "_daily" / f"{day}.json"
    digest = source_hash(cards)
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("source_hash") == digest and _valid_notes(cached.get("notes"), cards):
            return cached["notes"]
    except (OSError, ValueError):
        pass
    notes = []
    ordered = sorted(cards, key=lambda item: item["id"])
    for offset in range(0, len(ordered), 25):
        chunk = ordered[offset:offset + 25]
        facts = [{
            "id": card["id"], "title": card["title"],
            "conclusion": str(card.get("conclusion", ""))[:180],
            "overview": str(card.get("event_overview", ""))[:180],
            "topics": card.get("topics", []),
            "confirmed_group": card.get("event_group_id", ""),
        } for card in chunk]
        prompt = (
            "你是 AI 新闻编辑。仅依据输入卡片提取至多 3 条当天最重要的事实进展，"
            "只有非空 confirmed_group 相同的卡片才能说成同一事件；不推断未给出的结果。"
            "返回 JSON：{\"notes\":[{\"text\":\"事实概述\",\"card_ids\":[\"输入ID\"]}]}。"
            "每条必须引用 1–4 个输入 ID，文字不超过 160 字，不要 Markdown。\n"
            + json.dumps(facts, ensure_ascii=False)
        )
        data = _model_json(
            llm, prompt,
            lambda value: isinstance(value, dict) and _valid_notes(value.get("notes"), chunk),
        )
        notes.extend(data["notes"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump({"source_hash": digest, "notes": notes}, handle, ensure_ascii=False)
        temporary = Path(handle.name)
    os.replace(temporary, path)
    return notes


def _valid_notes(notes: Any, cards: list[dict[str, Any]]) -> bool:
    if not isinstance(notes, list) or not notes or len(notes) > max(3, ((len(cards) + 24) // 25) * 3):
        return False
    allowed = {card["id"] for card in cards}
    return all(
        isinstance(note, dict) and isinstance(note.get("text"), str)
        and 0 < len(note["text"].strip()) <= 200
        and isinstance(note.get("card_ids"), list) and 1 <= len(note["card_ids"]) <= 4
        and all(isinstance(card_id, str) and card_id in allowed for card_id in note["card_ids"])
        for note in notes
    )


def generate_report(
    markdown_root: Path, period: str, start: date, end: date,
    cards: list[dict[str, Any]], llm: Any, timezone: str,
) -> Path:
    if not cards or not getattr(llm, "available", False):
        raise ValueError("无已审核卡片或 AI 服务不可用")
    by_day: dict[str, list[dict[str, Any]]] = {}
    for card in cards:
        by_day.setdefault(card["event_date"], []).append(card)
    notes = []
    for day, day_cards in sorted(by_day.items()):
        notes.extend(_day_notes(markdown_root, day, day_cards, llm))
    prompt = (
        f"你是中文 AI 新闻编辑。请总结 {start} 至 {end} 的 AI 进展，"
        "只依据下列事实笔记写阶段性综述，不把未经确认的相似报道说成同一事件，"
        "只选最重要的 3–5 个共同主题，允许略去其他笔记；每条重点中的所有引用必须支撑同一个论点，"
        "不要为覆盖更多领域而拼接无关进展。对待核实的材料保留不确定性。"
        "不杜撰数据、因果或未来结果。写简短总述、3–5 条跨卡片的重点结论与趋势、"
        "至多 3 条后续关注，每条只写一个具体待验证问题；本期少于 3 张卡片时，按卡片数写结论。"
        "每条结论和关注项必须有 1–4 个事实笔记中的卡片 ID 支撑。"
        "只输出 JSON：{\"lead\":\"总述\",\"highlights\":[{\"text\":\"结论\",\"card_ids\":[\"ID\"]}],"
        "\"watch\":[{\"text\":\"关注点\",\"card_ids\":[\"ID\"]}]}。\n"
        + json.dumps(notes, ensure_ascii=False)
    )
    data = _model_json(llm, prompt, lambda value: valid_report(value, cards))
    data.update({
        "period": period, "start": start.isoformat(), "end": end.isoformat(),
        "source": "site_ai", "source_hash": source_hash(cards),
        "generated_at": datetime.now(ZoneInfo(timezone)).isoformat(timespec="minutes"),
    })
    path = write_report(markdown_root, period, start, data)
    failure_path(markdown_root, period, start).unlink(missing_ok=True)
    return path

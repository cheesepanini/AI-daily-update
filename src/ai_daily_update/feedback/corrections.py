from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from ai_daily_update.utils.lock import exclusive_file_lock


def correction_path(root: Path) -> Path:
    return root / "data" / "feedback" / "corrections.json"


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def card_fingerprint(metadata: dict[str, Any], content: str) -> str:
    return fingerprint({"title": metadata.get("title_zh"), "source_url": metadata.get("source_url"),
                        "event_date": metadata.get("event_date"),
                        "topics": metadata.get("topics"), "first_party": metadata.get("first_party"),
                        "research_links": metadata.get("research_links"),
                        "content": content})


def report_fingerprint(report: dict[str, Any]) -> str:
    return fingerprint({"lead": report.get("lead"), "source_hash": report.get("source_hash"),
                        "highlights": [(item.get("text"), item.get("card_ids")) for item in report.get("highlights", [])],
                        "watch": [(item.get("text"), item.get("card_ids")) for item in report.get("watch", [])]})


def read_corrections(root: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(correction_path(root).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def change_corrections(root: Path, change):
    path = correction_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with exclusive_file_lock(path.with_suffix(".lock"), blocking=True):
        items = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        if not isinstance(items, list):
            raise ValueError("correction store must contain a list")
        result = change(items)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        os.replace(temporary, path)
    return result


def submit_correction(root: Path, kind: str, target: str, message: str, current_hash: str, created_at: str) -> str:
    item_id = uuid.uuid4().hex[:16]
    def add(items):
        items.append({"id": item_id, "kind": kind, "target": target, "message": message,
                      "original_hash": current_hash, "created_at": created_at, "status": "pending"})
    change_corrections(root, add)
    return item_id


def decide_correction(root: Path, item_id: str, status: str, summary: str, now: str) -> bool:
    def change(items):
        for item in items:
            if item.get("id") == item_id and item.get("status") == "pending":
                item.update(status=status, summary=summary if status == "resolved" else "", resolved_at=now)
                return True
        return False
    return change_corrections(root, change)


def public_revisions(root: Path, kind: str, target: str) -> list[dict[str, Any]]:
    return [item for item in read_corrections(root)
            if item.get("kind") == kind and item.get("target") == target and item.get("status") == "resolved"]

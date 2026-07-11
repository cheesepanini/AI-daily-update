from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from ai_daily_update.utils.dates import now_iso


def feedback_log_path(root: Path) -> Path:
    return root / "data" / "feedback" / "events.jsonl"


def append_feedback_event(
    root: Path,
    timezone: str,
    surface: str,
    entity_type: str,
    entity_id: str,
    action: str,
    *,
    actor: str = "user",
    previous_status: str = "",
    new_status: str = "",
    source: str = "web",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": f"feedback-{uuid.uuid4().hex[:12]}",
        "created_at": now_iso(timezone),
        "actor": actor,
        "source": source,
        "surface": surface,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "previous_status": previous_status,
        "new_status": new_status,
        "feature_version": "v1",
        "metadata": metadata or {},
    }
    path = feedback_log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def read_feedback_events(root: Path) -> list[dict[str, Any]]:
    path = feedback_log_path(root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # One truncated/corrupted line (e.g. from a crash mid-write)
            # should not take down every reader of this append-only log:
            # the web preference dashboard and preference-feature
            # extraction both depend on being able to read the rest of it.
            continue
    return events

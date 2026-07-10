from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in_timezone(timezone: str) -> date:
    return datetime.now(ZoneInfo(timezone)).date()


def now_iso(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")

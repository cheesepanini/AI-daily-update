from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in_timezone(timezone: str) -> date:
    return datetime.now(ZoneInfo(timezone)).date()


def now_iso(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).isoformat(timespec="seconds")


def normalize_iso_date(value: str) -> str | None:
    text = value.strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def public_date_fields(metadata: dict) -> dict[str, str]:
    dates = metadata.get("news_dates", {})
    event = normalize_iso_date(str(dates.get("event") or "")) or ""
    reported = normalize_iso_date(str(dates.get("reported") or "")) or ""
    legacy = ""
    if "news_dates" not in metadata:
        legacy = normalize_iso_date(str(metadata.get("event_date") or metadata.get("date") or "")) or ""
    if event:
        label = "事件日期"
    elif reported:
        label = "报道日期"
    elif legacy:
        label = "旧记录日期 · 待核实"
    else:
        label = "日期待核实"
    return {"confirmed_event_date": event, "reported_date": reported, "legacy_date": legacy,
            "display_date": event or reported or legacy, "date_label": label}
